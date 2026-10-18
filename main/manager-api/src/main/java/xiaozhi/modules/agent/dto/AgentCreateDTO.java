package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Agent creation DTO
 * Used only when creating agents; it does not contain the id, agentCode and sort fields, which the system generates or sets to default values
 */
@Data
@Schema(description = "Agent creation object")
public class AgentCreateDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Agent name", example = "Customer service assistant")
    @NotBlank(message = "Agent name cannot be empty")
    private String agentName;
}