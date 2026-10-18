package xiaozhi.common.service;

import java.io.Serializable;
import java.util.Collection;

import com.baomidou.mybatisplus.core.conditions.Wrapper;

/**
 * Base service interface; all service interfaces must extend it
 * Copyright (c) Renren Open Source All rights reserved.
 * Website: https://www.renren.io
 */
public interface BaseService<T> {
    Class<T> currentModelClass();

    /**
     * <p>
     * Insert one record (with field selection and insert strategy)
     * </p>
     *
     * @param entity Entity object
     */
    boolean insert(T entity);

    /**
     * <p>
     * Batch insert; this method does not support Oracle or SQL Server
     * </p>
     *
     * @param entityList Entity collection
     */
    boolean insertBatch(Collection<T> entityList);

    /**
     * <p>
     * Batch insert; this method does not support Oracle or SQL Server
     * </p>
     *
     * @param entityList Entity collection
     * @param batchSize  Insert batch size
     */
    boolean insertBatch(Collection<T> entityList, int batchSize);

    /**
     * <p>
     * Update by ID with field selection
     * </p>
     *
     * @param entity Entity object
     */
    boolean updateById(T entity);

    /**
     * <p>
     * Update records matching the whereEntity condition
     * </p>
     *
     * @param entity        Entity object
     * @param updateWrapper Entity wrapper class
     *                      {@link com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper}
     */
    boolean update(T entity, Wrapper<T> updateWrapper);

    /**
     * <p>
     * Batch update by ID
     * </p>
     *
     * @param entityList Entity collection
     */
    boolean updateBatchById(Collection<T> entityList);

    /**
     * <p>
     * Batch update by ID
     * </p>
     *
     * @param entityList Entity collection
     * @param batchSize  Update batch size
     */
    boolean updateBatchById(Collection<T> entityList, int batchSize);

    /**
     * <p>
     * Query by ID
     * </p>
     *
     * @param id Primary key ID
     */
    T selectById(Serializable id);

    /**
     * <p>
     * Delete by ID
     * </p>
     *
     * @param id Primary key ID
     */
    boolean deleteById(Serializable id);

    /**
     * <p>
     * Delete (batch delete by ID)
     * </p>
     *
     * @param idList Primary key ID list
     */
    boolean deleteBatchIds(Collection<? extends Serializable> idList);
}