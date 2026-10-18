package xiaozhi.modules.llm.service;

/**
 * LLM service interface
 * Supports calls to multiple LLMs
 */
public interface LLMService {

    /**
     * Generates a chat history summary.
     * 
     * @param conversation   conversation content
     * @param promptTemplate prompt template
     * @return summary result
     */
    String generateSummary(String conversation, String promptTemplate);

    /**
     * Generates a chat history summary (using the default prompt).
     * 
     * @param conversation conversation content
     * @return summary result
     */
    String generateSummary(String conversation);

    /**
     * Generates a chat history summary (with a specified model ID).
     * 
     * @param conversation conversation content
     * @param modelId      model ID
     * @return summary result
     */
    String generateSummaryWithModel(String conversation, String modelId);

    /**
     * Generates a chat history summary (with a specified model ID and prompt template).
     * 
     * @param conversation   conversation content
     * @param promptTemplate prompt template
     * @param modelId        model ID
     * @return summary result
     */
    String generateSummary(String conversation, String promptTemplate, String modelId);

    /**
     * Generates a chat history summary (including merging of historical memory).
     * 
     * @param conversation   conversation content
     * @param historyMemory  historical memory
     * @param promptTemplate prompt template
     * @param modelId        model ID
     * @return summary result
     */
    String generateSummaryWithHistory(String conversation, String historyMemory, String promptTemplate, String modelId);

    /**
     * Checks whether the service is available.
     * 
     * @return whether it is available
     */
    boolean isAvailable();

    /**
     * Checks whether the service of the specified model is available.
     * 
     * @param modelId model ID
     * @return whether it is available
     */
    boolean isAvailable(String modelId);

    /**
     * Generates a session title.
     * 
     * @param conversation conversation content
     * @param modelId      model ID
     * @return title (about 15 characters)
     */
    String generateTitle(String conversation, String modelId);
}
