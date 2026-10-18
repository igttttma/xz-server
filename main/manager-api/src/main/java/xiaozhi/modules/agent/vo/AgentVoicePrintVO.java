package xiaozhi.modules.agent.vo;

import lombok.Data;

import java.util.Date;

/**
 * VO for displaying the agent voiceprint list
 */
@Data
public class AgentVoicePrintVO {

    /**
     * Primary key ID
     */
    private String id;
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
    /**
     * Creation time
     */
    private Date createDate;
}
