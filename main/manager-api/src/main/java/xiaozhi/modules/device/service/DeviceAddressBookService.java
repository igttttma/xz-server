package xiaozhi.modules.device.service;

import java.util.List;
import java.util.Map;

import xiaozhi.modules.device.entity.DeviceAddressBookEntity;

public interface DeviceAddressBookService {

    /**
     * Get the device address book list
     */
    List<DeviceAddressBookEntity> getAddressBookList(String macAddress);

    /**
     * Get the address book of all devices (for the global cache)
     */
    Map<String, Map<String, String>> getAllAddressBooks();

    /**
     * Update the alias
     */
    void updateAlias(String macAddress, String targetMac, String alias);

    /**
     * Update permissions
     */
    void updatePermission(String macAddress, String targetMac, Boolean hasPermission);

    /**
     * Add or update the address book record
     */
    void saveOrUpdate(String macAddress, String targetMac, String alias, Boolean hasPermission);

    /**
     * Refresh the address book cache
     */
    void refreshCache();

    /**
     * Start a call by nickname
     * @param callerMac Caller MAC address
     * @param nickname Callee nickname
     * @param isAnswer Whether in answer mode (skips the permission check)
     */
    Map<String, Object> callByNickname(String callerMac, String nickname, boolean isAnswer);

    /**
     * Batch delete the address book records related to the devices
     */
    void deleteByMacAddresses(List<String> macAddresses);
}