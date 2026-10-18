-- Fix the duplicate provider_code issue of Doubao TTS model 2.0 and add ASR 2.0 support

-- ==================== Doubao TTS model 2.0 ====================
-- Delete the TTS 2.0 provider (a separate provider is no longer needed)
delete from `ai_model_provider` where id = 'SYSTEM_TTS_HSDSTTS_V2';

-- ==================== Doubao ASR (streaming) ====================
-- Fix the existing Doubao streaming ASR provider by removing the cluster field and adding the resource_id field
UPDATE `ai_model_provider` SET `fields` = '[{"key":"appid","type":"string","label":"App ID"},{"key":"access_token","type":"string","label":"Access Token"},{"key":"boosting_table_name","type":"string","label":"Hotword File Name"},{"key":"correct_table_name","type":"string","label":"Replacement Word File Name"},{"key":"output_dir","type":"string","label":"Output Directory"},{"key":"end_window_size","type":"number","label":"Silence Detection Duration (ms)"},{"key":"enable_multilingual","type":"boolean","label":"Whether to Enable Multilingual Recognition Mode"},{"key":"language","type":"string","label":"Specify Language Code"},{"key":"resource_id","type":"string","label":"Resource ID"}]' WHERE `id` = 'SYSTEM_ASR_DoubaoStreamASR';

-- Fix the existing Doubao streaming ASR configuration by removing the cluster field and adding the resource_id default
UPDATE `ai_model_config` SET `config_json` = JSON_REMOVE(JSON_SET(`config_json`, '$.resource_id', 'volc.bigasr.sauc.duration'), '$.cluster') WHERE `id` = 'ASR_DoubaoStreamASR';

-- ==================== Doubao ASR model 2.0 ====================

-- Insert the Doubao ASR model 2.0 configuration
delete from `ai_model_config` where id = 'ASR_DoubaoStreamASRV2';
INSERT INTO `ai_model_config` VALUES ('ASR_DoubaoStreamASRV2', 'ASR', 'DoubaoStreamASRV2', 'Doubao ASR Model 2.0', 0, 1, '{
  "type": "doubao_stream",
  "appid": "",
  "access_token": "",
  "resource_id": "volc.seedasr.sauc.duration",
  "end_window_size": 200,
  "enable_multilingual": false,
  "language": "zh-CN",
  "output_dir": "tmp/"
}', NULL, NULL, 6, NULL, NULL, NULL, NULL);

-- Doubao ASR model 2.0 configuration documentation
UPDATE `ai_model_config` SET
`doc_link` = 'https://www.volcengine.com/docs/6561/109979',
`remark` = 'Doubao ASR Model 2.0 configuration (based on Volcano Engine seed-asr):
1. Visit https://www.volcengine.com/ to register and activate a Volcano Engine account
2. Visit https://console.volcengine.com/speech/service/10038 to enable Doubao streaming ASR Model 2.0
3. Obtain the appid and access_token at the bottom of the page
4. There are two resource ID types: hourly (volc.seedasr.sauc.duration) and concurrency-based (volc.seedasr.sauc.concurrent)
   - Hourly: fixed to volc.seedasr.sauc.duration (Doubao ASR Model 2.0)
   - Concurrency-based: fixed to volc.seedasr.sauc.concurrent (Doubao ASR Model 2.0)

Detailed parameter documentation: https://www.volcengine.com/docs/6561/109979

Notes:
- Doubao ASR Model 2.0 uses the volc.seedasr.sauc.duration resource ID, which differs from Doubao ASR (streaming) (volc.bigasr.sauc.duration)
- ASR Model 2.0 is cheaper; the concurrency-based resource ID is recommended for high-concurrency scenarios
' WHERE `id` = 'ASR_DoubaoStreamASRV2';
