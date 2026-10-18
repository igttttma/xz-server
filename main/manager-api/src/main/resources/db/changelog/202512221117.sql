-- Update the Doubao streaming ASR provider and add the end_window_size configuration
delete from `ai_model_provider` where id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', 'Volcano Engine Speech Recognition (Streaming)', '[{"key":"appid","label":"App ID","type":"string"},{"key":"access_token","label":"Access Token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Hotword File Name","type":"string"},{"key":"correct_table_name","label":"Replacement Word File Name","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"end_window_size","label":"Silence Detection Duration (ms)","type":"number"}]', 3, 1, NOW(), 1, NOW());


-- Update the Doubao streaming ASR model configuration and add the end_window_size default
UPDATE `ai_model_config` SET
`config_json` = JSON_SET(`config_json`, '$.end_window_size', 200)
WHERE `id` = 'ASR_DoubaoStreamASR' AND JSON_EXTRACT(`config_json`, '$.end_window_size') IS NULL;
