package xiaozhi.modules.agent.service;

import xiaozhi.common.service.BaseService;
import xiaozhi.modules.agent.entity.AgentContextProviderEntity;

public interface AgentContextProviderService extends BaseService<AgentContextProviderEntity> {
    /**
     * Get the context provider configuration by agent ID
     * @param agentId Agent ID
     * @return Context provider configuration entity
     */
    AgentContextProviderEntity getByAgentId(String agentId);

    /**
     * Save or update the context provider configuration
     * @param entity Entity
     */
    void saveOrUpdateByAgentId(AgentContextProviderEntity entity);

    /**
     * Delete the context provider configuration by agent ID
     * @param agentId Agent ID
     */
    void deleteByAgentId(String agentId);
}
