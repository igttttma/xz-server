package xiaozhi.modules.agent.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import org.apache.ibatis.annotations.Select;
import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.vo.AgentInfoVO;

@Mapper
public interface AgentDao extends BaseDao<AgentEntity> {
    /**
     * Get the device count of the agent
     * 
     * @param agentId Agent ID
     * @return Device count
     */
    Integer getDeviceCountByAgentId(@Param("agentId") String agentId);

    /**
     * Look up the default agent information of the device by MAC address
     *
     * @param macAddress Device MAC address
     * @return Default agent information
     */
    @Select(" SELECT a.* FROM ai_device d " +
            " LEFT JOIN ai_agent a ON d.agent_id = a.id " +
            " WHERE d.mac_address = #{macAddress} " +
            " ORDER BY d.id DESC LIMIT 1")
    AgentEntity getDefaultAgentByMacAddress(@Param("macAddress") String macAddress);

    /**
     * Query agent information by ID, including plugin information
     *
     * @param agentId Agent ID
     */
    AgentInfoVO selectAgentInfoById(@Param("agentId") String agentId);

    /**
     * Lock the agent master record to serialize configuration writes for the same agent
     *
     * @param agentId Agent ID
     */
    AgentEntity selectByIdForUpdate(@Param("agentId") String agentId);

    /**
     * Write exactly the agent fields covered by the snapshot, including null values from the target snapshot.
     * Fields that do not belong to the snapshot, such as the owner and creation information, are not updated.
     *
     * @param agent Agent to which the target snapshot has been applied
     * @return Number of affected rows
     */
    int updateSnapshotFields(@Param("agent") AgentEntity agent);
}
