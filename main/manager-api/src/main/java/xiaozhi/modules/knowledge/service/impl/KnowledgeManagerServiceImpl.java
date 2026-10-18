package xiaozhi.modules.knowledge.service.impl;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;
import xiaozhi.modules.knowledge.service.KnowledgeManagerService;

import java.util.List;

@Service
@Slf4j
@RequiredArgsConstructor
public class KnowledgeManagerServiceImpl implements KnowledgeManagerService {

    private final KnowledgeBaseService knowledgeBaseService;
    private final KnowledgeFilesService knowledgeFilesService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteDatasetWithFiles(String datasetId) {
        log.info("=== Cascade delete started: datasetId={} ===", datasetId);

        // 1. Call the file service first to clean up all document records of this dataset (including the RAGFlow side)
        log.info("Step 1: Cleaning up associated documents...");
        knowledgeFilesService.deleteDocumentsByDatasetId(datasetId);

        // 2. Then call the knowledge base service to fully deregister the dataset (including the RAGFlow side)
        log.info("Step 2: Deleting the dataset entity...");
        knowledgeBaseService.deleteByDatasetId(datasetId);

        log.info("=== Cascade delete succeeded: datasetId={} ===", datasetId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void batchDeleteDatasetsWithFiles(List<String> datasetIds) {
        if (datasetIds == null || datasetIds.isEmpty())
            return;
        log.info("=== Batch cascade delete started: count={} ===", datasetIds.size());
        for (String id : datasetIds) {
            deleteDatasetWithFiles(id);
        }
    }
}
