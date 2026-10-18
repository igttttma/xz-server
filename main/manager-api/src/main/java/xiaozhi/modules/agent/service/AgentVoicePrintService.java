package xiaozhi.modules.agent.service;

import java.util.List;

import xiaozhi.modules.agent.dto.AgentVoicePrintSaveDTO;
import xiaozhi.modules.agent.dto.AgentVoicePrintUpdateDTO;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;

/**
 * Agent voiceprint service
 *
 * @author zjy
 */
public interface AgentVoicePrintService {
    /**
     * Add a new voiceprint for the agent
     *
     * @param dto Voiceprint data to save for the agent
     * @return T: success, F: failure
     */
    boolean insert(AgentVoicePrintSaveDTO dto);

    /**
     * Delete the specified voiceprint of the agent
     *
     * @param userId       ID of the currently logged-in user
     * @param voicePrintId Voiceprint ID
     * @return Whether successful: T - success, F - failure
     */
    boolean delete(Long userId, String voicePrintId);

    /**
     * Get all voiceprint data of the specified agent
     *
     * @param userId  ID of the currently logged-in user
     * @param agentId Agent ID
     * @return Voiceprint data collection
     */
    List<AgentVoicePrintVO> list(Long userId, String agentId);

    /**
     * Update the specified voiceprint data of the agent
     *
     * @param userId ID of the currently logged-in user
     * @param dto    Voiceprint data to update
     * @return Whether successful: T - success, F - failure
     */
    boolean update(Long userId, AgentVoicePrintUpdateDTO dto);

}
