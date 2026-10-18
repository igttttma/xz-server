package xiaozhi.modules.agent.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * VO for a user's personal chat data of an agent
 */
@Data
public class AgentChatHistoryUserVO {
    @Schema(description = "Chat content")
    private String content;

    @Schema(description = "Audio ID")
    private String audioId;
}
