package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Update the device address book alias")
public class DeviceAddressBookAliasDTO {

    @NotBlank(message = "MAC address cannot be empty")
    @Schema(description = "Local device MAC address")
    private String macAddress;

    @NotBlank(message = "Target MAC address cannot be empty")
    @Schema(description = "Peer device MAC address")
    private String targetMac;

    @Schema(description = "My nickname for the peer")
    private String alias;
}