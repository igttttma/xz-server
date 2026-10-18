package xiaozhi.modules.sys.service;


import java.util.function.Consumer;

/**
 * Defines a system user utility service to avoid circular dependencies with the user module,
 * for example when users and devices depend on each other: users need to fetch all devices,
 * and devices need to fetch the username of each device.
 * @author zjy
 * @since 2025-4-2
 */
public interface SysUserUtilService {
    /**
     * Assign the username
     * @param userId user id
     * @param setter setter method
     */
    void assignUsername( Long userId, Consumer<String> setter);
}
