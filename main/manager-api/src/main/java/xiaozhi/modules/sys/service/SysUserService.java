package xiaozhi.modules.sys.service;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.AdminPageUserDTO;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.entity.SysUserEntity;
import xiaozhi.modules.sys.vo.AdminPageUserVO;

/**
 * System user
 */
public interface SysUserService extends BaseService<SysUserEntity> {

    SysUserDTO getByUsername(String username);

    SysUserDTO getByUserId(Long userId);

    void save(SysUserDTO dto);

    /**
     * Delete the specified user along with the associated devices and agents
     * 
     * @param ids
     */
    void deleteById(Long ids);

    /**
     * Verify whether the password change is allowed
     * 
     * @param userId      user id
     * @param passwordDTO parameters for password verification
     */
    void changePassword(Long userId, PasswordDTO passwordDTO);

    /**
     * Change the password directly without verification
     * 
     * @param userId   user id
     * @param password password
     */
    void changePasswordDirectly(Long userId, String password);

    /**
     * Reset the password
     * 
     * @param userId user id
     * @return a randomly generated password that meets the requirements
     */
    String resetPassword(Long userId);

    /**
     * Page through user information for administrators
     * 
     * @param dto paging query parameters
     * @return paged user list data
     */
    PageData<AdminPageUserVO> page(AdminPageUserDTO dto);

    /**
     * Batch update user status
     * 
     * @param status  user status
     * @param userIds user ID array
     */
    void changeStatus(Integer status, String[] userIds);

    /**
     * Get whether user registration is allowed
     * 
     * @return whether user registration is allowed
     */
    boolean getAllowUserRegister();
}
