package xiaozhi.modules.device.service;

import java.util.Date;
import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.device.dto.DeviceManualAddDTO;
import xiaozhi.modules.device.dto.DevicePageUserDTO;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.vo.UserShowDeviceListVO;

public interface DeviceService extends BaseService<DeviceEntity> {
    /**
     * Get the device online data
     */
    String getDeviceOnlineData(String agentId);

    /**
     * Check whether the device is activated
     */
    DeviceReportRespDTO checkDeviceActive(String macAddress, String clientId,
            DeviceReportReqDTO deviceReport);

    /**
     * Get the device list of the agent specified by the user,
     */
    List<DeviceEntity> getUserDevices(Long userId, String agentId);

    /**
     * Get the device list of the agent specified by the user (with time zone handling),
     */
    List<UserShowDeviceListVO> getUserDeviceList(Long userId, String agentId);

    /**
     * Unbind the device
     */
    void unbindDevice(Long userId, String deviceId);

    /**
     * Device activation
     */
    Boolean deviceActivation(String agentId, String activationCode);

    /**
     * Delete all devices of this user
     * 
     * @param userId User ID
     */
    void deleteByUserId(Long userId);

    /**
     * Delete all devices associated with the specified agent
     * 
     * @param agentId Agent ID
     */
    void deleteByAgentId(String agentId);

    /**
     * Get the device count of the specified user
     * 
     * @param userId User ID
     * @return Device count
     */
    Long selectCountByUserId(Long userId);

    /**
     * Get all device information with pagination
     *
     * @param dto Pagination query parameters
     * @return Paged user list data
     */
    PageData<UserShowDeviceListVO> page(DevicePageUserDTO dto);

    /**
     * Get device information by MAC address
     * 
     * @param macAddress MAC address
     * @return Device information
     */
    DeviceEntity getDeviceByMacAddress(String macAddress);

    /**
     * Get the activation code by device ID
     * 
     * @param deviceId Device ID
     * @return Activation code
     */
    String geCodeByDeviceId(String deviceId);

    /**
     * Get the most recent last connection time among the devices of this agent
     * 
     * @param agentId Agent ID
     * @return Return the device's most recent last connection time
     */
    Date getLatestLastConnectionTime(String agentId);

    /**
     * Manually add a device
     */
    void manualAddDevice(Long userId, DeviceManualAddDTO dto);

    /**
     * Update the device connection information
     */
    void updateDeviceConnectionInfo(String agentId, String deviceId, String appVersion);

    /**
     * Generate the WebSocket authentication token
     *
     * @param clientId Client ID
     * @param username Username (usually deviceId)
     * @return Authentication token string
     * @throws Exception Exception thrown while generating the token
     */
    String generateWebSocketToken(String clientId, String username) throws Exception;

    /**
     * Search devices by MAC address
     *
     * @param macAddress MAC address keyword
     * @param userId     User ID
     * @return Device list
     */
    List<DeviceEntity> searchDevicesByMacAddress(String macAddress, Long userId);

    /**
     * Get the device tool list
     */
    Object getDeviceTools(String deviceId);

    /**
     * Invoke a device tool
     */
    Object callDeviceTool(String deviceId, String toolName, Map<String, Object> arguments);

    }