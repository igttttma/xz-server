package xiaozhi.modules.agent.entity;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

/**
 * Agent configuration template table
 * 
 * @TableName ai_agent_template
 */
@TableName(value = "ai_agent_template")
@Data
public class AgentTemplateEntity implements Serializable {
    /**
     * Agent unique identifier
     */
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    /**
     * Agent code
     */
    private String agentCode;

    /**
     * Agent name
     */
    private String agentName;

    /**
     * ASR model ID
     */
    private String asrModelId;

    /**
     * VAD model ID
     */
    private String vadModelId;

    /**
     * LLM model ID
     */
    private String llmModelId;

    /**
     * VLLM model ID
     */
    private String vllmModelId;

    /**
     * TTS model ID
     */
    private String ttsModelId;

    /**
     * Voice ID
     */
    private String ttsVoiceId;

    /**
     * Voice language
     */
    private String ttsLanguage;

    /**
     * TTS volume
     */
    private Integer ttsVolume;

    /**
     * TTS speed
     */
    private Integer ttsRate;

    /**
     * TTS pitch
     */
    private Integer ttsPitch;

    /**
     * Memory model ID
     */
    private String memModelId;

    /**
     * Intent model ID
     */
    private String intentModelId;

    /**
     * Chat history configuration (0: do not record, 1: text only, 2: text and audio)
     */
    private Integer chatHistoryConf;

    /**
     * Role setting parameters
     */
    private String systemPrompt;

    /**
     * Summary memory
     */
    private String summaryMemory;
    /**
     * Language code
     */
    private String langCode;

    /**
     * Interaction language
     */
    private String language;

    /**
     * Sort weight
     */
    private Integer sort;

    /**
     * Creator ID
     */
    private Long creator;

    /**
     * Creation time
     */
    private Date createdAt;

    /**
     * Updater ID
     */
    private Long updater;

    /**
     * Update time
     */
    private Date updatedAt;

    @TableField(exist = false)
    private static final long serialVersionUID = 1L;
}