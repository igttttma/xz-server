-- Change the memory model name

UPDATE `ai_model_config` SET `model_name` = 'Local Short-term Memory (Summarized Memory)' WHERE `id` = 'Memory_mem_local_short';
UPDATE `ai_model_provider` SET `name` = 'Local Short-term Memory (Summarized Memory)' WHERE `id` = 'SYSTEM_Memory_mem_local_short';

UPDATE `ai_model_config` SET `model_name` = 'Report Chat History Only (No Memory Summary)' WHERE `id` = 'Memory_mem_report_only';
UPDATE `ai_model_provider` SET `name` = 'Report Chat History Only (No Memory Summary)' WHERE `id` = 'SYSTEM_Memory_mem_report_only';
