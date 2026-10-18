package xiaozhi.modules.sys.service;

import java.util.List;
import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.sys.dto.SysDictDataDTO;
import xiaozhi.modules.sys.entity.SysDictDataEntity;
import xiaozhi.modules.sys.vo.SysDictDataItem;
import xiaozhi.modules.sys.vo.SysDictDataVO;

/**
 * Data dictionary
 */
public interface SysDictDataService extends BaseService<SysDictDataEntity> {

    /**
     * Page through data dictionary information
     *
     * @param params query parameters, including pagination information and query conditions
     * @return the paged query result of the data dictionary
     */
    PageData<SysDictDataVO> page(Map<String, Object> params);

    /**
     * Get a data dictionary entity by ID
     *
     * @param id the unique identifier of the data dictionary entity
     * @return the detailed information of the data dictionary entity
     */
    SysDictDataVO get(Long id);

    /**
     * Save a new data dictionary entry
     *
     * @param dto the data transfer object for saving a data dictionary entry
     */
    void save(SysDictDataDTO dto);

    /**
     * Update a data dictionary entry
     *
     * @param dto the data transfer object for updating a data dictionary entry
     */
    void update(SysDictDataDTO dto);

    /**
     * Delete data dictionary entries
     *
     * @param ids the ID array of the data dictionary entries to delete
     */
    void delete(Long[] ids);

    /**
     * Delete the corresponding dictionary data by dictionary type ID
     *
     * @param dictTypeId dictionary type ID
     */
    void deleteByTypeId(Long dictTypeId);

    /**
     * Get the dictionary data list by dictionary type
     *
     * @param dictType dictionary type
     * @return the dictionary data list
     */
    List<SysDictDataItem> getDictDataByType(String dictType);

}