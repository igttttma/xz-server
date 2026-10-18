-- Add the Baidu ASR model configuration
delete from `ai_model_config` where `id` = 'ASR_BaiduASR';
INSERT INTO `ai_model_config` VALUES ('ASR_BaiduASR', 'ASR', 'BaiduASR', 'Baidu Speech Recognition', 0, 1, '{\"type\": \"baidu\", \"app_id\": \"\", \"api_key\": \"\", \"secret_key\": \"\", \"dev_pid\": 1537, \"output_dir\": \"tmp/\"}', NULL, NULL, 7, NULL, NULL, NULL, NULL);


-- Add the Baidu ASR provider
delete from `ai_model_provider` where `id` = 'SYSTEM_ASR_BaiduASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_BaiduASR', 'ASR', 'baidu', 'Baidu Speech Recognition', '[{"key":"app_id","label":"App AppID","type":"string"},{"key":"api_key","label":"API Key","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"dev_pid","label":"Language Parameter","type":"number"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 7, 1, NOW(), 1, NOW());


-- Update the Baidu ASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list',
`remark` = 'Baidu ASR configuration:
1. Visit https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list
2. Create a new application
3. Obtain the AppID, API Key and Secret Key
4. Fill them into the configuration file
Check the resource quota at: https://console.bce.baidu.com/ai-engine/old/#/ai/speech/overview/resource/list
Language parameter documentation: https://ai.baidu.com/ai-doc/SPEECH/0lbxfnc9b
' WHERE `id` = 'ASR_BaiduASR';

-- Update the Doubao provider fields
update `ai_model_provider` set `fields` = 
'[{"key":"appid","label":"App ID","type":"string"},{"key":"access_token","label":"Access Token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Hotword File Name","type":"string"},{"key":"correct_table_name","label":"Replacement Word File Name","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]'
where `id` = 'SYSTEM_ASR_DoubaoASR';

-- Update the Doubao ASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Doubao ASR configuration:
1. Create an application in the Volcano Engine console and obtain the appid and access_token
2. Supports Chinese speech recognition
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create a new application
3. Obtain the appid and access_token
4. Fill them into the configuration file
To set hotwords, see: https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoASR';