package xiaozhi.modules.voiceclone.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.voiceclone.dto.VoiceCloneDTO;
import xiaozhi.modules.voiceclone.dto.VoiceCloneResponseDTO;
import xiaozhi.modules.voiceclone.entity.VoiceCloneEntity;

/**
 * Voice cloning management
 */
public interface VoiceCloneService extends BaseService<VoiceCloneEntity> {

    /**
     * Page through
     */
    PageData<VoiceCloneEntity> page(Map<String, Object> params);

    /**
     * Save a voice clone
     */
    void save(VoiceCloneDTO dto);

    /**
     * Batch delete
     */
    void delete(String[] ids);

    /**
     * Get the voice cloning list by user ID
     * 
     * @param userId user ID
     * @return voice cloning list
     */
    List<VoiceCloneEntity> getByUserId(Long userId);

    /**
     * Page through the voice cloning list with model and user names
     */
    PageData<VoiceCloneResponseDTO> pageWithNames(Map<String, Object> params);

    /**
     * Get the voice cloning information with model and user names by ID
     */
    VoiceCloneResponseDTO getByIdWithNames(String id);

    /**
     * Get the voice cloning list with model names by user ID
     */
    List<VoiceCloneResponseDTO> getByUserIdWithNames(Long userId);

    /**
     * Upload an audio file
     */
    void uploadVoice(String id, MultipartFile voiceFile) throws Exception;

    /**
     * Update the voice cloning name
     */
    void updateName(String id, String name);

    /**
     * Get the audio data
     */
    byte[] getVoiceData(String id);

    /**
     * Clone audio by calling Volcano Engine for voice cloning training
     * 
     * @param cloneId voice cloning record ID
     */
    void cloneAudio(String cloneId);
}
