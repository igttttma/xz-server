package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * DTO for saving the agent voiceprint
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintSaveDTO {
    /**
     * Associated agent ID
     */
    private String agentId;
    /**
     * Audio file ID
     */
    private String audioId;
    /**
     * Name of the person the voiceprint comes from
     */
    private String sourceName;
    /**
     * Describe the person the voiceprint comes from
     */
    private String introduce;
}
