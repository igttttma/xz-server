-- VLLM model provider
delete from `ai_model_provider` where id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', 'Volcano Engine Speech Recognition (Streaming)', '[{"key":"appid","label":"App ID","type":"string"},{"key":"access_token","label":"Access Token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Hotword File Name","type":"string"},{"key":"correct_table_name","label":"Replacement Word File Name","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 3, 1, NOW(), 1, NOW());


-- VLLM model configuration
delete from `ai_model_config` where id = 'ASR_DoubaoStreamASR';
INSERT INTO `ai_model_config` VALUES ('ASR_DoubaoStreamASR', 'ASR', 'DoubaoStreamASR', 'Doubao Speech Recognition (Streaming)', 0, 1, '{\"type\": \"doubao_stream\", \"appid\": \"\", \"access_token\": \"\", \"cluster\": \"volcengine_input_common\", \"output_dir\": \"tmp/\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);


-- Update the Doubao ASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Doubao ASR configuration:
1. The difference between Doubao ASR and Doubao (streaming) ASR is that Doubao ASR is billed per request, while Doubao (streaming) ASR is billed by time
2. Per-request billing is generally cheaper, but Doubao (streaming) ASR uses large model technology and performs better
3. Create an application in the Volcano Engine console and obtain the appid and access_token
4. Supports Chinese speech recognition
5. Network connection required
6. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create a new application
3. Obtain the appid and access_token
4. Fill them into the configuration file
To set hotwords, see: https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoASR';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Doubao ASR configuration:
1. The difference between Doubao ASR and Doubao (streaming) ASR is that Doubao ASR is billed per request, while Doubao (streaming) ASR is billed by time
2. Per-request billing is generally cheaper, but Doubao (streaming) ASR uses large model technology and performs better
3. Create an application in the Volcano Engine console and obtain the appid and access_token
4. Supports Chinese speech recognition
5. Network connection required
6. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create a new application
3. Obtain the appid and access_token
4. Fill them into the configuration file
To set hotwords, see: https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoStreamASR';
