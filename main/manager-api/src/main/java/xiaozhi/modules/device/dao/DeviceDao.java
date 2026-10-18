package xiaozhi.modules.device.dao;

import java.util.Date;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.device.entity.DeviceEntity;

@Mapper
public interface DeviceDao extends BaseMapper<DeviceEntity> {
    /**
     * Get the last connection time of all devices of this agent
     * 
     * @param agentId Agent ID
     * @return
     */
    Date getAllLastConnectedAtByAgentId(String agentId);

}