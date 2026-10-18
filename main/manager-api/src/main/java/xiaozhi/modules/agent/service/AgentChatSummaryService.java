package xiaozhi.modules.agent.service;

/**
 * Agent chat history summary service interface
 */
public interface AgentChatSummaryService {

    /**
     * Generate a chat history summary by session ID and save it to the agent memory
     * 
     * @param sessionId Session ID
     * @return Save result
     */
    boolean generateAndSaveChatSummary(String sessionId);

    /**
     * Generate and save the chat title by session ID
     *
     * @param sessionId Session ID
     * @return Whether successful
     */
    boolean generateAndSaveChatTitle(String sessionId);
}