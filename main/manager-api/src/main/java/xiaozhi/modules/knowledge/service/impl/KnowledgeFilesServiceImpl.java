package xiaozhi.modules.knowledge.service.impl;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.ErrorCode;
import org.springframework.util.CollectionUtils;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.modules.knowledge.dao.DocumentDao;
import xiaozhi.modules.knowledge.entity.DocumentEntity;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapter;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapterFactory;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;

@Service
@Slf4j
public class KnowledgeFilesServiceImpl extends BaseServiceImpl<DocumentDao, DocumentEntity>
        implements KnowledgeFilesService {

    private final KnowledgeBaseService knowledgeBaseService;
    private final DocumentDao documentDao;
    private final ObjectMapper objectMapper;
    private final RedisUtils redisUtils;

    public KnowledgeFilesServiceImpl(KnowledgeBaseService knowledgeBaseService,
            DocumentDao documentDao,
            ObjectMapper objectMapper,
            RedisUtils redisUtils) {
        this.knowledgeBaseService = knowledgeBaseService;
        this.documentDao = documentDao;
        this.objectMapper = objectMapper;
        this.redisUtils = redisUtils;
    }

    @Lazy
    @Autowired
    private KnowledgeFilesService self;

    @Override
    public Map<String, Object> getRAGConfig(String ragModelId) {
        return knowledgeBaseService.getRAGConfig(ragModelId);
    }

    @Override
    public PageData<KnowledgeFilesDTO> getPageList(KnowledgeFilesDTO knowledgeFilesDTO, Integer page, Integer limit) {
        log.info("=== Starting to get the knowledge base document list (Local-First optimized version) ===");
        String datasetId = knowledgeFilesDTO.getDatasetId();
        if (StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        // Full reconciliation synchronization: pull remote documents from RAGFlow and synchronize in real time to perceive remote changes immediately
        try {
            self.syncDocumentsFromRAG(datasetId);
        } catch (Exception e) {
            log.warn("Failed to fully synchronize documents from RAGFlow (does not affect local queries): datasetId={}, error={}", datasetId, e.getMessage());
        }

        // 1. Get local shadow table data (MyBatis-Plus paging)
        Page<DocumentEntity> pageParams = new Page<>(page, limit);
        QueryWrapper<DocumentEntity> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("dataset_id", datasetId);
        if (StringUtils.isNotBlank(knowledgeFilesDTO.getName())) {
            queryWrapper.like("name", knowledgeFilesDTO.getName());
        }
        if (StringUtils.isNotBlank(knowledgeFilesDTO.getRun())) {
            queryWrapper.eq("run", knowledgeFilesDTO.getRun());
        }
        if (StringUtils.isNotBlank(knowledgeFilesDTO.getStatus())) {
            queryWrapper.eq("status", knowledgeFilesDTO.getStatus());
        }
        queryWrapper.orderByDesc("created_at");

        // 2. Execute the local query
        Page<DocumentEntity> iPage = documentDao.selectPage(pageParams, queryWrapper);

        // 3. Convert the DTOs manually
        List<KnowledgeFilesDTO> dtoList = new ArrayList<>();
        for (DocumentEntity entity : iPage.getRecords()) {
            dtoList.add(convertEntityToDTO(entity));
        }
        PageData<KnowledgeFilesDTO> pageData = new PageData<>(dtoList, iPage.getTotal());

        // 4. Dynamic status synchronization (with rate limiting and protection)
        // [Bug Fix] P1: expand the synchronization whitelist so CANCEL/FAIL also allow low-frequency synchronization for self-healing
        if (pageData.getList() != null && !pageData.getList().isEmpty()) {
            KnowledgeBaseAdapter adapter = null;
            for (KnowledgeFilesDTO dto : pageData.getList()) {
                String runStatus = dto.getRun();
                // High-priority synchronization: RUNNING/UNSTART (5-second cooldown)
                boolean isActiveSync = "RUNNING".equals(runStatus) || "UNSTART".equals(runStatus);
                // Low-frequency self-healing synchronization: CANCEL/FAIL (60-second cooldown), prevents error states from being locked forever
                boolean isRecoverySync = "CANCEL".equals(runStatus) || "FAIL".equals(runStatus);
                boolean needSync = isActiveSync || isRecoverySync;

                if (needSync) {
                    // Rate-limit protection: 5-second cooldown for active states, 60-second cooldown for self-healing states
                    long cooldownMs = isActiveSync ? 5000 : 60000;
                    DocumentEntity localEntity = documentDao.selectOne(new QueryWrapper<DocumentEntity>()
                            .eq("document_id", dto.getDocumentId()));
                    if (localEntity != null && localEntity.getLastSyncAt() != null) {
                        long diff = System.currentTimeMillis() - localEntity.getLastSyncAt().getTime();
                        if (diff < cooldownMs) {
                            continue;
                        }
                    }

                    // Lazily initialize the adapter, creating it only when synchronization is really needed
                    if (adapter == null) {
                        try {
                            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
                            adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);
                        } catch (Exception e) {
                            log.warn("Synchronization interrupted: unable to initialize the adapter, {}", e.getMessage());
                            break;
                        }
                    }
                    // [Critical Fix] Record the token count before synchronization to compute the delta
                    Long oldTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;

                    syncDocumentStatusWithRAG(dto, adapter);

                    // Compute the delta and update the knowledge base statistics (consistent with the scheduled task)
                    Long newTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;
                    Long tokenDelta = newTokenCount - oldTokenCount;
                    if (tokenDelta != 0) {
                        knowledgeBaseService.updateStatistics(datasetId, 0, 0L, tokenDelta);
                        log.info("Lazy-load synchronization: corrected knowledge base statistics, docId={}, tokenDelta={}", dto.getDocumentId(), tokenDelta);
                    }
                }
            }
        }

        log.info("Document list retrieved successfully, total: {}", pageData.getTotal());
        return pageData;
    }

    /**
     * Converts a local record entity into a DTO, manually aligning inconsistent fields (size -> fileSize, type -> fileType).
     */
    private KnowledgeFilesDTO convertEntityToDTO(DocumentEntity entity) {
        if (entity == null) {
            return null;
        }
        KnowledgeFilesDTO dto = new KnowledgeFilesDTO();
        // 1. Copy the basic fields
        BeanUtils.copyProperties(entity, dto);

        // Issue 2: Fix the ID semantics. The frontend tends to use id as the operation primary key.
        // In this module, the remote documentId should always be mapped to the DTO id, ensuring consistent IDs for frontend operations such as details/deletion.
        dto.setId(entity.getDocumentId());

        // 2. Convert the local record entity into a DTO, manually aligning inconsistent fields (size -> fileSize, type -> fileType)
        dto.setFileSize(entity.getSize());
        dto.setFileType(entity.getType());
        dto.setRun(entity.getRun());
        dto.setChunkCount(entity.getChunkCount());
        dto.setTokenCount(entity.getTokenCount());
        dto.setError(entity.getError());

        // 3. Deserialize the custom metadata JSON (Issue 3)
        if (StringUtils.isNotBlank(entity.getMetaFields())) {
            try {
                dto.setMetaFields(objectMapper.readValue(entity.getMetaFields(),
                        new TypeReference<Map<String, Object>>() {
                        }));
            } catch (Exception e) {
                log.warn("Failed to deserialize MetaFields, entityId: {}, error: {}", entity.getId(), e.getMessage());
            }
        }

        // 4. Deserialize the parser configuration JSON
        if (StringUtils.isNotBlank(entity.getParserConfig())) {
            try {
                dto.setParserConfig(objectMapper.readValue(entity.getParserConfig(),
                        new com.fasterxml.jackson.core.type.TypeReference<Map<String, Object>>() {
                        }));
            } catch (Exception e) {
                log.warn("Failed to deserialize ParserConfig, entityId: {}, error: {}", entity.getId(), e.getMessage());
            }
        }
        return dto;

    }

    /**
     * Synchronizes the document status with the actual RAG status.
     * Optimizes the status synchronization logic so that the "parsing" state is displayed correctly.
     * Only when the document has chunks and parsing has taken more than 30 seconds is it updated to the completed state.
     */
    /**
     * Synchronizes the document status with the actual RAG status (enhanced: supports passing in an external adapter).
     */
    private void syncDocumentStatusWithRAG(KnowledgeFilesDTO dto, KnowledgeBaseAdapter adapter) {
        if (dto == null || StringUtils.isBlank(dto.getDocumentId()) || adapter == null) {
            return;
        }

        String documentId = dto.getDocumentId();
        String datasetId = dto.getDatasetId();

        try {
            // Use the strongly typed ListReq with ID filtering to obtain the status
            DocumentDTO.ListReq listReq = DocumentDTO.ListReq.builder()
                    .id(documentId)
                    .page(1)
                    .pageSize(1)
                    .build();

            PageData<KnowledgeFilesDTO> remoteList = adapter.getDocumentList(datasetId, listReq);

            if (remoteList != null && remoteList.getList() != null && !remoteList.getList().isEmpty()) {
                KnowledgeFilesDTO remoteDto = remoteList.getList().get(0);
                String remoteStatus = remoteDto.getStatus();

                // Core status alignment decision logic
                boolean statusChanged = remoteStatus != null && !remoteStatus.equals(dto.getStatus());
                boolean runChanged = remoteDto.getRun() != null && !remoteDto.getRun().equals(dto.getRun());
                boolean isProcessing = "RUNNING".equals(remoteDto.getRun()) || "UNSTART".equals(remoteDto.getRun());

                // As long as the status has changed, the run status has changed, or the file is still being parsed (real-time progress refresh), perform synchronization
                if (statusChanged || runChanged || isProcessing) {
                    log.info("Shadow synchronization: statusChanged={}, processing={}, document={}, latestStatus={}, progress={}",
                            statusChanged, isProcessing, documentId, remoteStatus, remoteDto.getProgress());

                    // 1. Synchronize the in-memory DTO
                    dto.setStatus(remoteStatus);
                    dto.setRun(remoteDto.getRun());
                    dto.setProgress(remoteDto.getProgress());
                    dto.setChunkCount(remoteDto.getChunkCount());
                    dto.setTokenCount(remoteDto.getTokenCount());
                    dto.setError(remoteDto.getError());
                    dto.setProcessDuration(remoteDto.getProcessDuration());
                    dto.setThumbnail(remoteDto.getThumbnail());

                    // 2. Synchronize the local shadow table
                    UpdateWrapper<DocumentEntity> updateWrapper = new UpdateWrapper<DocumentEntity>()
                            .set("status", remoteStatus)
                            .set("run", remoteDto.getRun())
                            .set("progress", remoteDto.getProgress())
                            .set("chunk_count", remoteDto.getChunkCount())
                            .set("token_count", remoteDto.getTokenCount())
                            .set("error", remoteDto.getError())
                            .set("process_duration", remoteDto.getProcessDuration())
                            .set("thumbnail", remoteDto.getThumbnail())
                            .eq("document_id", documentId)
                            .eq("dataset_id", datasetId);

                    // Serialize and synchronize the metadata
                    if (remoteDto.getMetaFields() != null) {
                        try {
                            updateWrapper.set("meta_fields",
                                    objectMapper.writeValueAsString(remoteDto.getMetaFields()));
                        } catch (Exception e) {
                            log.warn("Failed to serialize metadata during synchronization: {}", e.getMessage());
                        }
                    }

                    // Prefer synchronizing the update time from the RAG side to avoid the local synchronization overwriting the business modification time
                    Date lastUpdate = remoteDto.getUpdatedAt() != null ? remoteDto.getUpdatedAt() : new Date();
                    updateWrapper.set("updated_at", lastUpdate);
                    updateWrapper.set("last_sync_at", new Date()); // Record the shadow DB synchronization time

                    documentDao.update(null, updateWrapper);
                }
            } else {
                // Issue 6: The remote list is empty; the document may have been deleted, or the adapter call may have gone wrong
                // [Bug Fix] P2: mark CANCEL only when the remote side truly returned a legitimate empty list
                // Also update last_sync_at, working with the P1 cooldown mechanism to prevent frequent misjudgments
                log.warn("Remote synchronization perception: RAGFlow returned an empty document list, docId={}, current local status={}",
                        documentId, dto.getRun());
                dto.setRun("CANCEL");
                dto.setError("The document has been deleted in the remote service");

                documentDao.update(null, new UpdateWrapper<DocumentEntity>()
                        .set("run", "CANCEL")
                        .set("error", "The document has been deleted in the remote service")
                        .set("updated_at", new Date())
                        .set("last_sync_at", new Date())
                        .eq("document_id", documentId));
            }
        } catch (Exception e) {
            // [Bug Fix] P2: do not mark CANCEL when the adapter call throws, to avoid misjudgments caused by network/deserialization issues
            // Only log and retry in the next synchronization cycle
            log.warn("Adapter call failed while synchronizing document status (CANCEL not marked), documentId: {}, error: {}",
                    documentId, e.getMessage());
        }
    }

    @Override
    public DocumentDTO.InfoVO getByDocumentId(String documentId, String datasetId) {
        if (StringUtils.isBlank(documentId) || StringUtils.isBlank(datasetId)) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        log.info("=== Starting to get the document by documentId ===");
        log.info("documentId: {}, datasetId: {}", documentId, datasetId);

        try {
            // Get the RAG configuration
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);

            // Extract the adapter type
            String adapterType = extractAdapterType(ragConfig);

            // Obtain an adapter instance from the adapter factory
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(adapterType, ragConfig);

            // Use the adapter to get the document details
            DocumentDTO.InfoVO info = adapter.getDocumentById(datasetId, documentId);

            if (info != null) {
                log.info("Document details retrieved successfully, documentId: {}", documentId);
                return info;
            } else {
                throw new RenException(ErrorCode.Knowledge_Base_RECORD_NOT_EXISTS);
            }

        } catch (Exception e) {
            log.error("Failed to get the document by documentId: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== Get document by documentId operation finished ===");
        }
    }

    @Override
    public KnowledgeFilesDTO uploadDocument(String datasetId, MultipartFile file, String name,
            Map<String, Object> metaFields, String chunkMethod,
            Map<String, Object> parserConfig) {
        if (StringUtils.isBlank(datasetId) || file == null || file.isEmpty()) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }

        log.info("=== Starting document upload operation (strong consistency optimized) ===");

        // 1. Preparation (non-transactional)
        String fileName = StringUtils.isNotBlank(name) ? name : file.getOriginalFilename();
        if (StringUtils.isBlank(fileName)) {
            throw new RenException(ErrorCode.RAG_FILE_NAME_NOT_NULL);
        }

        log.info("1. Initiating remote upload: datasetId={}, fileName={}", datasetId, fileName);

        // Get the adapter (non-transactional)
        Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
        KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);

        // Build the strongly typed request DTO
        DocumentDTO.UploadReq uploadReq = DocumentDTO.UploadReq.builder()
                .datasetId(datasetId)
                .file(file)
                .name(fileName)
                .metaFields(metaFields)
                .build();

        // Convert the chunking method (String -> Enum)
        if (StringUtils.isNotBlank(chunkMethod)) {
            try {
                uploadReq.setChunkMethod(DocumentDTO.InfoVO.ChunkMethod.valueOf(chunkMethod.toUpperCase()));
            } catch (Exception e) {
                log.warn("Invalid chunking method: {}, the backend default configuration will be used", chunkMethod);
            }
        }

        // Convert the parser configuration (Map -> DTO)
        if (parserConfig != null && !parserConfig.isEmpty()) {
            uploadReq.setParserConfig(objectMapper.convertValue(parserConfig, DocumentDTO.InfoVO.ParserConfig.class));
        }

        // Execute the remote upload (time-consuming IO, outside the transaction)
        KnowledgeFilesDTO result = adapter.uploadDocument(uploadReq);

        if (result == null || StringUtils.isBlank(result.getDocumentId())) {
            throw new RenException(ErrorCode.RAG_API_ERROR, "Remote upload succeeded but no valid DocumentID was returned");
        }

        // 2. Local persistence (invoked through self to activate the @Transactional proxy)
        log.info("2. Synchronously saving the local shadow record: documentId={}", result.getDocumentId());
        self.saveDocumentShadow(datasetId, result, fileName, chunkMethod, parserConfig);

        log.info("=== Document upload and shadow record save succeeded ===");
        return result;
    }

    /**
     * Atomically saves the shadow record (Upsert semantics).
     * If document_id already exists it is updated, otherwise it is inserted, avoiding UNIQUE constraint conflicts.
     *
     * @return true = newly inserted, false = existing record updated
     */
    @Transactional(rollbackFor = Exception.class)
    public boolean saveDocumentShadow(String datasetId, KnowledgeFilesDTO result, String originalName, String chunkMethod,
            Map<String, Object> parserConfig) {
        DocumentEntity entity = new DocumentEntity();
        entity.setDatasetId(datasetId);
        entity.setDocumentId(result.getDocumentId());
        entity.setName(StringUtils.isNotBlank(result.getName()) ? result.getName() : originalName);
        entity.setSize(result.getFileSize());
        entity.setType(getFileType(entity.getName()));
        entity.setChunkMethod(chunkMethod);

        if (parserConfig != null) {
            try {
                entity.setParserConfig(objectMapper.writeValueAsString(parserConfig));
            } catch (Exception e) {
                log.warn("Failed to serialize the parser configuration: {}", e.getMessage());
            }
        }

        entity.setStatus(result.getStatus() != null ? result.getStatus() : "1");
        entity.setRun(result.getRun());
        entity.setProgress(result.getProgress());
        entity.setThumbnail(result.getThumbnail());
        entity.setProcessDuration(result.getProcessDuration());
        entity.setSourceType(result.getSourceType());
        entity.setError(result.getError());
        entity.setChunkCount(result.getChunkCount());
        entity.setTokenCount(result.getTokenCount());
        entity.setEnabled(1);

        // Persist the metadata
        if (result.getMetaFields() != null) {
            try {
                entity.setMetaFields(objectMapper.writeValueAsString(result.getMetaFields()));
            } catch (Exception e) {
                log.warn("Failed to persist the shadow metadata: {}", e.getMessage());
            }
        }

        // Prefer synchronizing the timestamps from the RAG side; otherwise use the local time
        entity.setCreatedAt(result.getCreatedAt() != null ? result.getCreatedAt() : new Date());
        entity.setUpdatedAt(result.getUpdatedAt() != null ? result.getUpdatedAt() : new Date());

        // Upsert: check whether document_id already exists; update if it does, insert otherwise
        DocumentEntity existing = documentDao.selectOne(
                new QueryWrapper<DocumentEntity>().eq("document_id", entity.getDocumentId()));

        if (existing != null) {
            entity.setId(existing.getId());
            entity.setCreatedAt(existing.getCreatedAt()); // Keep the original creation time
            documentDao.updateById(entity);
            log.info("Shadow record updated: documentId={}", entity.getDocumentId());
            return false;
        } else {
            documentDao.insert(entity);
            // Increment the dataset document count statistics when a record is added
            knowledgeBaseService.updateStatistics(datasetId, 1, 0L, 0L);
            log.info("Shadow record inserted: documentId={}, datasetId={}", entity.getDocumentId(), datasetId);
            return true;
        }
    }

    @Override
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void deleteDocuments(String datasetId, DocumentDTO.BatchIdReq req) {
        if (StringUtils.isBlank(datasetId) || req == null || req.getIds() == null || req.getIds().isEmpty()) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        List<String> documentIds = req.getIds();
        log.info("=== Starting batch document deletion: datasetId={}, count={} ===", datasetId, documentIds.size());

        // 1. Batch permission and status pre-check
        List<DocumentEntity> entities = documentDao.selectList(
                new QueryWrapper<DocumentEntity>()
                        .eq("dataset_id", datasetId)
                        .in("document_id", documentIds));

        if (entities.size() != documentIds.size()) {
            log.warn("Some documents do not exist or have ownership issues: expected={}, actual={}", documentIds.size(), entities.size());
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        long totalChunkDelta = 0;
        long totalTokenDelta = 0;

        for (DocumentEntity entity : entities) {
            // Intercept deletion requests for documents that are being parsed
            // [Bug Fix] The run field (RUNNING) should be used to determine "parsing", not the status field
            // status="1" means "enabled/normal", not "parsing"
            if ("RUNNING".equals(entity.getRun())) {
                log.warn("Intercepted the deletion request of a file being parsed: docId={}", entity.getDocumentId());
                throw new RenException(ErrorCode.RAG_DOCUMENT_PARSING_DELETE_ERROR);
            }
            totalChunkDelta += entity.getChunkCount() != null ? entity.getChunkCount() : 0L;
            totalTokenDelta += entity.getTokenCount() != null ? entity.getTokenCount() : 0L;
        }

        // 2. Get the adapter (non-transactional)
        Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
        KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);

        // 3. Execute the remote deletion
        try {
            adapter.deleteDocument(datasetId, req);
            log.info("Remote batch deletion request succeeded");
        } catch (Exception e) {
            log.error("Remote deletion request failed, aborting local cleanup to avoid data inconsistency: {}", e.getMessage());
            throw new RenException(e.getMessage());
        }

        // 4. Atomically clean up the local shadow records and synchronize the statistics
        self.deleteDocumentShadows(documentIds, datasetId, totalChunkDelta, totalTokenDelta);

        // 5. Clean up the cache
        try {
            String cacheKey = RedisKeys.getKnowledgeBaseCacheKey(datasetId);
            redisUtils.delete(cacheKey);
            log.info("Dataset cache evicted: {}", cacheKey);
        } catch (Exception e) {
            log.warn("Failed to evict the Redis cache: {}", e.getMessage());
        }

        log.info("=== Batch document cleanup complete ===");
    }

    /**
     * Atomically deletes shadow records in batch and synchronizes the parent table statistics.
     */
    @Transactional(rollbackFor = Exception.class)
    public void deleteDocumentShadows(List<String> documentIds, String datasetId, Long chunkDelta, Long tokenDelta) {
        // 1. Physically delete the records
        int deleted = documentDao.delete(
                new QueryWrapper<DocumentEntity>()
                        .eq("dataset_id", datasetId)
                        .in("document_id", documentIds));

        if (deleted > 0) {
            // 2. Synchronously update the dataset statistics
            knowledgeBaseService.updateStatistics(datasetId, -documentIds.size(), -chunkDelta, -tokenDelta);
            log.info("Dataset statistics decremented: datasetId={}, chunks={}, tokens={}", datasetId, chunkDelta, tokenDelta);
        }
    }

    /**
     * Gets the file type - supports the four RAG document format types.
     */
    private String getFileType(String fileName) {
        if (StringUtils.isBlank(fileName)) {
            log.warn("File name is empty, returning the unknown type");
            return "unknown";
        }

        try {
            int lastDotIndex = fileName.lastIndexOf('.');
            if (lastDotIndex > 0 && lastDotIndex < fileName.length() - 1) {
                String extension = fileName.substring(lastDotIndex + 1).toLowerCase();

                // Document format types
                String[] documentTypes = { "pdf", "doc", "docx", "txt", "md", "mdx" };
                String[] spreadsheetTypes = { "csv", "xls", "xlsx" };
                String[] presentationTypes = { "ppt", "pptx" };

                // Check document types
                for (String type : documentTypes) {
                    if (type.equals(extension)) {
                        return "document";
                    }
                }

                // Check spreadsheet types
                for (String type : spreadsheetTypes) {
                    if (type.equals(extension)) {
                        return "spreadsheet";
                    }
                }
                // Check presentation types
                for (String type : presentationTypes) {
                    if (type.equals(extension)) {
                        return "presentation";
                    }
                }
                // Return the original extension as the file type
                return extension;
            }
            return "unknown";
        } catch (Exception e) {
            log.error("Failed to get the file type: ", e);
            return "unknown";
        }
    }

    /**
     * Extracts the adapter type from the RAG configuration.
     */
    private String extractAdapterType(Map<String, Object> config) {
        if (config == null) {
            throw new RenException(ErrorCode.RAG_CONFIG_NOT_FOUND);
        }

        // Extract the type field from the configuration
        String adapterType = (String) config.get("type");
        if (StringUtils.isBlank(adapterType)) {
            throw new RenException(ErrorCode.RAG_ADAPTER_TYPE_NOT_FOUND);
        }

        // Verify whether the adapter type is registered
        if (!KnowledgeBaseAdapterFactory.isAdapterTypeRegistered(adapterType)) {
            throw new RenException(ErrorCode.RAG_ADAPTER_TYPE_NOT_SUPPORTED, "Adapter type is not registered: " + adapterType);
        }

        return adapterType;
    }

    @Override
    public boolean parseDocuments(String datasetId, List<String> documentIds) {
        if (StringUtils.isBlank(datasetId) || documentIds == null || documentIds.isEmpty()) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        log.info("=== Starting document parsing (chunking) ===");
        log.info("datasetId: {}, documentIds: {}", datasetId, documentIds);

        try {
            // Get the RAG configuration
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);

            // Extract the adapter type
            String adapterType = extractAdapterType(ragConfig);

            // Get the knowledge base adapter
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(adapterType, ragConfig);

            log.debug("Parse document parameters: documentIds: {}", documentIds);

            // Call the adapter to parse the documents
            boolean result = adapter.parseDocuments(datasetId, documentIds);

            if (result) {
                log.info("Document parsing command sent successfully, preparing to synchronize the local shadow DB status, datasetId: {}, documentIds: {}", datasetId, documentIds);
                // Immediately update the local shadow status to RUNNING and parsing(1) after the command succeeds, so the Local-First list reflects it immediately
                documentDao.update(null, new UpdateWrapper<DocumentEntity>()
                        .set("run", "RUNNING")
                        .set("status", "1")
                        .set("updated_at", new Date())
                        .eq("dataset_id", datasetId)
                        .in("document_id", documentIds));

                log.info("Local document status updated to RUNNING");
            } else {
                log.error("Document parsing failed, datasetId: {}, documentIds: {}", datasetId, documentIds);
                throw new RenException(ErrorCode.RAG_API_ERROR, "Document parsing failed");
            }

            return result;

        } catch (Exception e) {
            log.error("Failed to parse documents: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== Parse document operation finished ===");
        }
    }

    @Override
    public ChunkDTO.ListVO listChunks(String datasetId, String documentId, ChunkDTO.ListReq req) {
        if (StringUtils.isBlank(datasetId) || StringUtils.isBlank(documentId)) {
            throw new RenException(ErrorCode.RAG_DATASET_ID_AND_MODEL_ID_NOT_NULL);
        }

        log.info("=== Starting to list chunks: datasetId={}, documentId={}, req={} ===", datasetId, documentId, req);

        try {
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig),
                    ragConfig);

            ChunkDTO.ListVO result = adapter.listChunks(datasetId, documentId, req);
            log.info("Chunk list retrieved successfully: datasetId={}, total={}", datasetId, result.getTotal());
            return result;
        } catch (Exception e) {
            log.error("Failed to list chunks: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== List chunks operation finished ===");
        }
    }

    @Override
    public RetrievalDTO.ResultVO retrievalTest(RetrievalDTO.TestReq req) {
        if (CollectionUtils.isEmpty(req.getDatasetIds())) {
            throw new RenException("No knowledge base specified for the retrieval test");
        }

        log.info("=== Starting retrieval test: req={} ===", req);

        try {
            Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(req.getDatasetIds().get(0));
            KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig),
                    ragConfig);

            RetrievalDTO.ResultVO result = adapter.retrievalTest(req);
            log.info("Retrieval test succeeded: total={}", result != null ? result.getTotal() : 0);
            return result;
        } catch (Exception e) {
            log.error("Retrieval test failed: {}", e.getMessage(), e);
            String errorMessage = e.getMessage() != null ? e.getMessage() : "null";
            if (e instanceof RenException) {
                throw (RenException) e;
            }
            throw new RenException(ErrorCode.RAG_API_ERROR, errorMessage);
        } finally {
            log.info("=== Retrieval test operation finished ===");
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteDocumentsByDatasetId(String datasetId) {
        log.info("Cascade cleanup of dataset documents: datasetId={}", datasetId);
        List<DocumentEntity> list = documentDao
                .selectList(new QueryWrapper<DocumentEntity>().eq("dataset_id", datasetId));
        if (list == null || list.isEmpty())
            return;

        List<String> docIds = list.stream().map(DocumentEntity::getDocumentId).toList();

        // Wrap and call the existing deletion logic (including RAG physical deletion)
        DocumentDTO.BatchIdReq req = DocumentDTO.BatchIdReq.builder().ids(docIds).build();
        this.deleteDocuments(datasetId, req);
    }

    @Override
    public int syncDocumentsFromRAG(String datasetId) {
        log.info("=== Starting full synchronization of documents from RAGFlow to the local shadow table: datasetId={} ===", datasetId);

        // 1. Get the adapter
        Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
        KnowledgeBaseAdapter adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);

        // 2. Page through all remote documents
        List<KnowledgeFilesDTO> allRemoteDocs = new ArrayList<>();
        int pageNum = 1;
        int pageSize = 100;
        long totalRemote = Long.MAX_VALUE;

        while ((long) (pageNum - 1) * pageSize < totalRemote) {
            DocumentDTO.ListReq req = DocumentDTO.ListReq.builder()
                    .page(pageNum)
                    .pageSize(pageSize)
                    .build();
            PageData<KnowledgeFilesDTO> remotePage = adapter.getDocumentList(datasetId, req);
            if (remotePage == null || remotePage.getList() == null || remotePage.getList().isEmpty()) {
                break;
            }
            allRemoteDocs.addAll(remotePage.getList());
            totalRemote = remotePage.getTotal();
            pageNum++;
        }

        // 3. Get the existing local documents
        List<DocumentEntity> localDocs = documentDao.selectList(
                new QueryWrapper<DocumentEntity>().eq("dataset_id", datasetId));
        Set<String> localDocIds = localDocs.stream()
                .map(DocumentEntity::getDocumentId)
                .collect(Collectors.toSet());

        // 4. Set of remote document IDs
        Set<String> remoteDocIds = allRemoteDocs.stream()
                .map(KnowledgeFilesDTO::getDocumentId)
                .filter(id -> id != null)
                .collect(Collectors.toSet());

        // 5. Supplement: insert documents that exist remotely but are missing locally
        List<KnowledgeFilesDTO> newDocs = allRemoteDocs.stream()
                .filter(doc -> doc.getDocumentId() != null && !localDocIds.contains(doc.getDocumentId()))
                .collect(Collectors.toList());

        int syncCount = 0;
        if (!newDocs.isEmpty()) {
            for (KnowledgeFilesDTO doc : newDocs) {
                try {
                    self.saveDocumentShadow(datasetId, doc, doc.getName(), doc.getChunkMethod(), doc.getParserConfig());
                    // Synchronize the token/chunk statistics that already exist remotely
                    Long tokenCount = doc.getTokenCount() != null ? doc.getTokenCount() : 0L;
                    long chunkCount = doc.getChunkCount() != null ? doc.getChunkCount().longValue() : 0L;
                    if (tokenCount > 0 || chunkCount > 0) {
                        knowledgeBaseService.updateStatistics(datasetId, 0, chunkCount, tokenCount);
                    }
                    syncCount++;
                } catch (Exception e) {
                    log.warn("Failed to synchronize a single document shadow record: docId={}, error={}", doc.getDocumentId(), e.getMessage());
                }
            }
            log.info("Newly synchronized {} document shadow records from RAGFlow, datasetId={}", syncCount, datasetId);
        }

        // 6. Cleanup: delete shadow records that no longer exist remotely but are still kept locally
        List<DocumentEntity> deletedDocs = localDocs.stream()
                .filter(entity -> !remoteDocIds.contains(entity.getDocumentId()))
                .collect(Collectors.toList());

        if (!deletedDocs.isEmpty()) {
            List<String> deletedDocIds = new ArrayList<>();
            long totalChunkDelta = 0;
            long totalTokenDelta = 0;

            for (DocumentEntity entity : deletedDocs) {
                deletedDocIds.add(entity.getDocumentId());
                totalChunkDelta += entity.getChunkCount() != null ? entity.getChunkCount() : 0L;
                totalTokenDelta += entity.getTokenCount() != null ? entity.getTokenCount() : 0L;
            }
            try {
                self.deleteDocumentShadows(deletedDocIds, datasetId, totalChunkDelta, totalTokenDelta);
                log.info("Cleaned up shadow records deleted remotely: {} items, datasetId={}", deletedDocs.size(), datasetId);
            } catch (Exception e) {
                log.warn("Failed to clean up shadow records deleted remotely: datasetId={}, error={}", datasetId, e.getMessage());
            }
        }

        // 7. Full update: for documents that exist both remotely and locally, synchronize all fields from the remote side
        // Handles scenarios such as RAGFlow re-uploading with the same documentId and metadata changes after remote edits
        Map<String, KnowledgeFilesDTO> remoteDocMap = allRemoteDocs.stream()
                .filter(doc -> doc.getDocumentId() != null)
                .collect(Collectors.toMap(KnowledgeFilesDTO::getDocumentId, doc -> doc, (a, b) -> b));

        Map<String, DocumentEntity> localDocMap = localDocs.stream()
                .collect(Collectors.toMap(DocumentEntity::getDocumentId, e -> e, (a, b) -> b));

        int updateCount = 0;
        for (Map.Entry<String, KnowledgeFilesDTO> entry : remoteDocMap.entrySet()) {
            String docId = entry.getKey();
            DocumentEntity local = localDocMap.get(docId);
            if (local == null) {
                continue; // Not present locally, handled by step 5
            }
            KnowledgeFilesDTO remote = entry.getValue();

            // Full field update (remote takes precedence) to ensure the local data matches RAGFlow exactly
            UpdateWrapper<DocumentEntity> updateWrapper = new UpdateWrapper<DocumentEntity>()
                    .set("run", remote.getRun())
                    .set("status", remote.getStatus() != null ? remote.getStatus() : local.getStatus())
                    .set("progress", remote.getProgress())
                    .set("chunk_count", remote.getChunkCount())
                    .set("token_count", remote.getTokenCount())
                    .set("size", remote.getFileSize())
                    .set("error", remote.getError())
                    .set("process_duration", remote.getProcessDuration())
                    .set("updated_at", new Date())
                    .set("last_sync_at", new Date())
                    .eq("document_id", docId)
                    .eq("dataset_id", datasetId);

            if (remote.getName() != null) {
                updateWrapper.set("name", remote.getName());
            }
            if (remote.getThumbnail() != null) {
                updateWrapper.set("thumbnail", remote.getThumbnail());
            }
            if (remote.getMetaFields() != null) {
                try {
                    updateWrapper.set("meta_fields", objectMapper.writeValueAsString(remote.getMetaFields()));
                } catch (Exception e) {
                    log.warn("Failed to serialize metadata during synchronization update: docId={}, error={}", docId, e.getMessage());
                }
            }

            documentDao.update(null, updateWrapper);

            // Synchronize the statistical differences (correct the parent table when the chunk/token counts change)
            Long remoteTokenCount = remote.getTokenCount() != null ? remote.getTokenCount() : 0L;
            Long localTokenCount = local.getTokenCount() != null ? local.getTokenCount() : 0L;
            long remoteChunkCount = remote.getChunkCount() != null ? remote.getChunkCount().longValue() : 0L;
            long localChunkCount = local.getChunkCount() != null ? local.getChunkCount().longValue() : 0L;
            long tokenDelta = remoteTokenCount - localTokenCount;
            long chunkDelta = remoteChunkCount - localChunkCount;
            if (tokenDelta != 0 || chunkDelta != 0) {
                knowledgeBaseService.updateStatistics(datasetId, 0, chunkDelta, tokenDelta);
                log.info("Shadow update: corrected knowledge base statistics, docId={}, chunkDelta={}, tokenDelta={}", docId, chunkDelta, tokenDelta);
            }

            updateCount++;
        }

        if (syncCount == 0 && deletedDocs.isEmpty() && updateCount == 0) {
            log.info("The local shadow table is fully synchronized with RAGFlow, datasetId={}", datasetId);
        } else {
            log.info("Synchronization complete: added={}, cleaned={}, updated={}, datasetId={}", syncCount, deletedDocs.size(), updateCount, datasetId);
        }

        return syncCount;
    }

    @Override
    public void syncRunningDocuments() {
        // 1. Query all documents in RUNNING state
        List<DocumentEntity> runningDocs = documentDao.selectList(
                new QueryWrapper<DocumentEntity>()
                        .eq("run", "RUNNING")
                        .eq("status", "1") // Only synchronize enabled documents
        );

        if (runningDocs == null || runningDocs.isEmpty()) {
            return;
        }

        log.info("Scheduled task: found {} documents being parsed, starting synchronization...", runningDocs.size());

        // 2. Group by DatasetID and reuse the Adapter
        Map<String, List<DocumentEntity>> groupedDocs = runningDocs.stream()
                .collect(Collectors.groupingBy(DocumentEntity::getDatasetId));

        groupedDocs.forEach((datasetId, docs) -> {
            KnowledgeBaseAdapter adapter = null;
            try {
                // Initialize the Adapter (only once per dataset)
                Map<String, Object> ragConfig = knowledgeBaseService.getRAGConfigByDatasetId(datasetId);
                adapter = KnowledgeBaseAdapterFactory.getAdapter(extractAdapterType(ragConfig), ragConfig);
            } catch (Exception e) {
                log.warn("Unable to initialize the adapter for dataset {}, skipping synchronization: {}", datasetId, e.getMessage());
                return;
            }

            for (DocumentEntity doc : docs) {
                try {
                    // Build a temporary DTO and pass it to the synchronization method
                    KnowledgeFilesDTO dto = convertEntityToDTO(doc);
                    // Record the token count before synchronization
                    Long oldTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;

                    syncDocumentStatusWithRAG(dto, adapter);

                    // 3. [Critical Fix] Compute the delta and update the knowledge base statistics
                    Long newTokenCount = dto.getTokenCount() != null ? dto.getTokenCount() : 0L;
                    Long tokenDelta = newTokenCount - oldTokenCount;

                    // Update the statistics only when the status becomes SUCCESS and the token count has changed
                    if (tokenDelta != 0) {
                        knowledgeBaseService.updateStatistics(datasetId, 0, 0L, tokenDelta);
                        log.info("Scheduled task: corrected knowledge base statistics during synchronization, docId={}, tokenDelta={}", dto.getDocumentId(), tokenDelta);
                    }
                } catch (Exception e) {
                    log.error("Failed to synchronize document {}: {}", doc.getDocumentId(), e.getMessage());
                }
            }
        });
    }
}
