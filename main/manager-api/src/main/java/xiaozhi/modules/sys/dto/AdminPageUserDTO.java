package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * DTO for the administrator paged user query
 * 
 * @author zjy
 * @since 2025-3-21
 */
@Data
@Schema(description = "DTO for the administrator paged user query")
public class AdminPageUserDTO {

    @Schema(description = "Mobile phone number")
    private String mobile;

    @Schema(description = "Page number")
    @Min(value = 0, message = "{sort.number}")
    private String page;

    @Schema(description = "Number of rows per page")
    @Min(value = 0, message = "{sort.number}")
    private String limit;
}
