package xiaozhi.modules.knowledge.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;

/**
 * Knowledge base document service interface
 */
public interface KnowledgeFilesService {

        /**
         * Page query of the document list.
         * 
         * @param knowledgeFilesDTO query conditions
         * @param page              page number
         * @param limit             number of items per page
         * @return paged data
         */
        PageData<KnowledgeFilesDTO> getPageList(KnowledgeFilesDTO knowledgeFilesDTO, Integer page, Integer limit);

        /**
         * Gets document details by document ID and knowledge base ID.
         * 
         * @param documentId document ID
         * @param datasetId  knowledge base ID
         * @return document details (strongly typed InfoVO)
         */
        DocumentDTO.InfoVO getByDocumentId(String documentId, String datasetId);

        /**
         * Uploads a document to the knowledge base.
         * 
         * @param datasetId    knowledge base ID
         * @param file         uploaded file
         * @param name         document name
         * @param metaFields   metadata fields
         * @param chunkMethod  chunking method
         * @param parserConfig parser configuration
         * @return information about the uploaded document
         */
        KnowledgeFilesDTO uploadDocument(String datasetId, MultipartFile file, String name,
                        Map<String, Object> metaFields, String chunkMethod,
                        Map<String, Object> parserConfig);

        /**
         * Batch deletes documents.
         * 
         * @param datasetId knowledge base ID
         * @param req       delete request parameters (containing the document ID list)
         */
        void deleteDocuments(String datasetId, DocumentDTO.BatchIdReq req);

        /**
         * Gets RAG configuration information.
         * 
         * @param ragModelId RAG model configuration ID
         * @return RAG configuration information
         */
        Map<String, Object> getRAGConfig(String ragModelId);

        /**
         * Parses documents (chunking).
         * 
         * @param datasetId   knowledge base ID
         * @param documentIds document ID list
         * @return parsing result
         */
        boolean parseDocuments(String datasetId, List<String> documentIds);

        /**
         * Lists the chunks of the specified document.
         * 
         * @param datasetId  knowledge base ID
         * @param documentId document ID
         * @param req        chunk list request parameters
         * @return chunk list information
         */
        ChunkDTO.ListVO listChunks(String datasetId, String documentId, ChunkDTO.ListReq req);

        /**
         * Retrieval test
         * 
         * @param req retrieval test request parameters
         * @return retrieval test result
         */
        RetrievalDTO.ResultVO retrievalTest(RetrievalDTO.TestReq req);

        /**
         * Saves the document shadow record.
         */
        boolean saveDocumentShadow(String datasetId, KnowledgeFilesDTO result, String originalName, String chunkMethod,
                        Map<String, Object> parserConfig);

        /**
         * Batch deletes document shadow records and synchronizes the statistics.
         * 
         * @param documentIds document ID list
         * @param datasetId   dataset ID
         * @param chunkDelta  total number of chunks to deduct
         * @param tokenDelta  total number of tokens to deduct
         */
        void deleteDocumentShadows(List<String> documentIds, String datasetId, Long chunkDelta, Long tokenDelta);

        /**
         * Cleans up all associated documents by dataset ID (used for cascade deletion).
         * 
         * @param datasetId dataset ID
         */
        void deleteDocumentsByDatasetId(String datasetId);

        /**
         * Synchronizes all documents in RUNNING state (invoked by the scheduled task).
         */
        void syncRunningDocuments();

        /**
         * Fully synchronizes documents from RAGFlow to the local shadow table.
         * Pulls all remote documents, compares them with the local shadow table and inserts missing records.
         *
         * @param datasetId dataset ID
         * @return number of newly synchronized documents
         */
        int syncDocumentsFromRAG(String datasetId);
}
