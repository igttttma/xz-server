package xiaozhi.modules.agent.service;

import com.baomidou.mybatisplus.extension.repository.IRepository;

import xiaozhi.modules.agent.entity.AgentTemplateEntity;

/**
 * @author chenerlei
 * @description Database Service for the table [ai_agent_template (agent configuration template table)]
 * @createDate 2025-03-22 11:48:18
 */
public interface AgentTemplateService extends IRepository<AgentTemplateEntity> {

    /**
     * Get the default template
     * 
     * @return Default template entity
     */
    AgentTemplateEntity getDefaultTemplate();

    /**
     * Update the model IDs in the default template
     * 
     * @param modelType Model type
     * @param modelId   Model ID
     */
    void updateDefaultTemplateModelId(String modelType, String modelId);

    /**
     * Reorder the remaining templates after deleting a template
     * 
     * @param deletedSort Sort value of the deleted template
     */
    void reorderTemplatesAfterDelete(Integer deletedSort);

    /**
     * Get the next available sort number (the smallest unused number)
     * 
     * @return Next available sort number
     */
    Integer getNextAvailableSort();
}
