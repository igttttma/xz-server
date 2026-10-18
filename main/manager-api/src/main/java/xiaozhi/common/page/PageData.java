package xiaozhi.common.page;

import java.io.Serializable;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Pagination utility
 * Copyright (c) Renren Open Source All rights reserved.
 * Website: https://www.renren.io
 */
@Data
@Schema(description = "Page data")
public class PageData<T> implements Serializable {
    @Schema(description = "Total record count")
    private int total;

    @Schema(description = "List data")
    private List<T> list;

    /**
     * Pagination
     *
     * @param list  List data
     * @param total Total record count
     */
    public PageData(List<T> list, long total) {
        this.list = list;
        this.total = (int) total;
    }
}