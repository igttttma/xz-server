package xiaozhi.modules.knowledge.service;

import java.util.List;

/**
 * Domain orchestration service for the knowledge base module.
 * Handles complex business flows that span KnowledgeBase and KnowledgeFiles, fully resolving circular dependencies between services.
 */
public interface KnowledgeManagerService {

    /**
     * Cascade-deletes a knowledge base and all of its documents (including local DB and RAGFlow remote data).
     * 
     * @param datasetId knowledge base ID
     */
    void deleteDatasetWithFiles(String datasetId);

    /**
     * Cascade-deletes knowledge bases in batch.
     * 
     * @param datasetIds list of knowledge base IDs
     */
    void batchDeleteDatasetsWithFiles(List<String> datasetIds);
}
