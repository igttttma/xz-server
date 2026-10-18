package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import xiaozhi.modules.sys.enums.ServerActionEnum;

/**
 * DTO for sending an operation to the Python server
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class EmitSeverActionDTO
{
    @Schema(description = "Target WebSocket address")
    @NotEmpty(message = "Target WebSocket address cannot be empty")
    private String targetWs;

    @Schema(description = "Operation to perform")
    @NotNull(message = "Operation cannot be empty")
    private ServerActionEnum action;
}
