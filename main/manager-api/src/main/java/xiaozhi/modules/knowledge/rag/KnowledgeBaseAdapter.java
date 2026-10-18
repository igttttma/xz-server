package xiaozhi.modules.knowledge.rag;

import java.util.List;
import java.util.Map;

import xiaozhi.modules.knowledge.dto.dataset.DatasetDTO;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import java.util.function.Consumer;

/**
 * Abstract base class of the knowledge base API adapter.
 * Defines the common knowledge base operation interface and supports multiple backend API implementations.
 */
public abstract class KnowledgeBaseAdapter {

        /**
         * Gets the adapter type identifier.
         * 
         * @return adapter type (e.g. ragflow, milvus, pinecone)
         */
        public abstract String getAdapterType();

        /**
         * Initializes the adapter configuration.
         * 
         * @param config configuration parameters
         */
        public abstract void initialize(Map<String, Object> config);

        /**
         * Validates whether the configuration is valid.
         * 
         * @param config configuration parameters
         * @return validation result
         */
        public abstract boolean validateConfig(Map<String, Object> config);

        /**
         * Page query of the document list.
         * 
         * @param datasetId   knowledge base ID
         * @param queryParams query parameters
         * @param page        page number
         * @param limit       number of items per page
         * @return paged data
         */
        public abstract PageData<KnowledgeFilesDTO> getDocumentList(String datasetId,
                        DocumentDTO.ListReq req);

        /**
         * Gets document details by document ID.
         * 
         * @param datasetId  knowledge base ID
         * @param documentId document ID
         * @return document details (strongly typed InfoVO)
         */
        public abstract DocumentDTO.InfoVO getDocumentById(String datasetId, String documentId);

        /**
         * Uploads a document to the knowledge base.
         * 
         * @param req upload request parameters
         * @return information about the uploaded document
         */
        public abstract KnowledgeFilesDTO uploadDocument(DocumentDTO.UploadReq req);

        /**
         * Page query of the document list by status.
         * 
         * @param datasetId knowledge base ID
         * @param status    document parsing status
         * @param page      page number
         * @param limit     number of items per page
         * @return paged data
         */
        public abstract PageData<KnowledgeFilesDTO> getDocumentListByStatus(String datasetId,
                        Integer status,
                        Integer page,
                        Integer limit);

        /**
         * Deletes documents (supports batch deletion).
         * 
         * @param datasetId knowledge base ID
         * @param req       request object containing the document ID list
         */
        public abstract void deleteDocument(String datasetId, DocumentDTO.BatchIdReq req);

        /**
         * Parses documents (chunking).
         * 
         * @param datasetId   knowledge base ID
         * @param documentIds document ID list
         * @return parsing result
         */
        public abstract boolean parseDocuments(String datasetId, List<String> documentIds);

        /**
         * Lists the chunks of the specified document.
         * 
         * @param datasetId  knowledge base ID
         * @param documentId document ID
         * @param req        list request parameters (paging, keywords, etc.)
         * @return chunk list VO
         */
        public abstract ChunkDTO.ListVO listChunks(String datasetId,
                        String documentId,
                        ChunkDTO.ListReq req);

        /**
         * Retrieval test - retrieves relevant chunks from the knowledge base.
         * 
         * @param req retrieval test request parameters
         * @return retrieval test result
         */
        public abstract RetrievalDTO.ResultVO retrievalTest(
                        RetrievalDTO.TestReq req);

        /**
         * Tests the connection.
         * 
         * @return connection test result
         */
        public abstract boolean testConnection();

        /**
         * Gets adapter status information.
         * 
         * @return status information
         */
        public abstract Map<String, Object> getStatus();

        /**
         * Gets the supported configuration parameters.
         * 
         * @return description of the configuration parameters
         */
        public abstract Map<String, Object> getSupportedConfig();

        /**
         * Gets the default configuration.
         * 
         * @return default configuration
         */
        public abstract Map<String, Object> getDefaultConfig();

        /**
         * Creates a dataset.
         * 
         * @param req creation parameters
         * @return dataset details
         */
        public abstract DatasetDTO.InfoVO createDataset(DatasetDTO.CreateReq req);

        /**
         * Updates a dataset.
         * 
         * @param datasetId dataset ID
         * @param req       update parameters
         * @return dataset details
         */
        public abstract DatasetDTO.InfoVO updateDataset(String datasetId, DatasetDTO.UpdateReq req);

        /**
         * Deletes datasets.
         * 
         * @param req delete request parameters (containing the ID list)
         * @return batch operation result
         */
        public abstract DatasetDTO.BatchOperationVO deleteDataset(DatasetDTO.BatchIdReq req);

        /**
         * Gets the number of documents in a dataset.
         *
         * @param datasetId dataset ID
         * @return number of documents
         */
        public abstract Integer getDocumentCount(String datasetId);

        /**
         * Gets the complete dataset information (name, description, document count, etc.).
         * Used to detect whether it has been deleted on the RAGFlow side and to synchronize name/description changes.
         *
         * @param datasetId dataset ID
         * @return dataset details, or null if it does not exist on the RAGFlow side
         */
        public abstract DatasetDTO.InfoVO getDatasetInfo(String datasetId);

        /**
         * Sends a streaming request (SSE).
         * 
         * @param endpoint API endpoint
         * @param body     request body
         * @param onData   data callback
         */
        public abstract void postStream(String endpoint, Object body, Consumer<String> onData);

        /**
         * SearchBot question.
         *
         * @param config RAG configuration
         * @param body   request body
         * @param onData data callback
         * @return response object
         */
        public abstract Object postSearchBotAsk(Map<String, Object> config, Object body,
                        Consumer<String> onData);

        /**
         * AgentBot conversation.
         *
         * @param config  RAG configuration
         * @param agentId Agent ID
         * @param body    request body
         * @param onData  data callback
         */
        public abstract void postAgentBotCompletion(Map<String, Object> config, String agentId, Object body,
                        Consumer<String> onData);
}
