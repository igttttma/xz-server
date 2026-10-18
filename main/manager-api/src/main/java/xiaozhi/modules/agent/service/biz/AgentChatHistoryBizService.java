package xiaozhi.modules.agent.service.biz;

import xiaozhi.modules.agent.dto.AgentChatHistoryReportDTO;

/**
 * Agent chat history business logic layer
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
public interface AgentChatHistoryBizService {

    /**
     * Chat reporting method
     *
     * @param agentChatHistoryReportDTO Input object containing the information required for chat reporting
     *                                  For example: device MAC address, file type, content, etc.
     * @return Upload result: true for success, false for failure
     */
    Boolean report(AgentChatHistoryReportDTO agentChatHistoryReportDTO);
}
