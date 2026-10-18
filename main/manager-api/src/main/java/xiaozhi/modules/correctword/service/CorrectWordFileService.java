package xiaozhi.modules.correctword.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.modules.correctword.dto.CorrectWordFileCreateDTO;
import xiaozhi.modules.correctword.vo.CorrectWordFileVO;
import xiaozhi.modules.correctword.vo.CorrectWordSimpleVO;

public interface CorrectWordFileService {

    /**
     * Create a replacement word file
     *
     * @param dto Create parameters
     * @return File VO
     */
    CorrectWordFileVO createFile(CorrectWordFileCreateDTO dto);

    /**
     * Update the replacement word file (full replacement of entries)
     *
     * @param fileId File ID
     * @param dto    Update parameters
     */
    void updateFile(String fileId, CorrectWordFileCreateDTO dto);

    /**
     * Get the current user's replacement word file list
     *
     * @param params Pagination parameters
     * @return Page data
     */
    PageData<CorrectWordFileVO> listFiles(Map<String, Object> params);

    /**
     * Get the current user's replacement word file list (unpaged, for dropdown selection)
     *
     * @return File list
     */
    List<CorrectWordFileVO> listAllFiles();

    /**
     * Get the original file content (for download)
     *
     * @param fileId File ID
     * @return File entity
     */
    CorrectWordFileVO getFileContent(String fileId);

    /**
     * Delete the replacement word file along with all its entries and association records
     *
     * @param fileId File ID
     */
    void deleteFile(String fileId);

    /**
     * Delete the association records of the agent's replacement word files (the files themselves are kept)
     *
     * @param agentId Agent ID
     */
    void deleteMappingsByAgentId(String agentId);

    /**
     * Get all replacement word entries of the agent (compact version for devices)
     *
     * @param agentId Agent ID
     * @return Replacement word list
     */
    List<CorrectWordSimpleVO> getAllItemsByAgentId(String agentId);

    /**
     * Get the IDs of the replacement word files associated with the agent
     *
     * @param agentId Agent ID
     * @return File ID list
     */
    List<String> getAgentCorrectWordFileIds(String agentId);

    /**
     * Save the replacement word files associated with the agent (full replacement)
     *
     * @param agentId Agent ID
     * @param fileIds File ID list
     */
    void saveAgentCorrectWords(String agentId, List<String> fileIds);

    /**
     * Batch delete replacement word files
     *
     * @param fileIds File ID list
     */
    void batchDeleteFiles(List<String> fileIds);
}
