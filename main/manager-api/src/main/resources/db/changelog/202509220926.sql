-- Add the iFlytek streaming ASR service configuration
delete from `ai_model_provider` where id = 'SYSTEM_ASR_XunfeiStream';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_XunfeiStream', 'ASR', 'xunfei_stream', 'iFlytek Streaming Speech Recognition', '[{"key":"app_id","label":"App ID","type":"string"},{"key":"api_key","label":"API_KEY","type":"password"},{"key":"api_secret","label":"API_SECRET","type":"password"},{"key":"domain","label":"Recognition Domain","type":"string"},{"key":"language","label":"Recognition Language","type":"string"},{"key":"accent","label":"Dialect","type":"string"},{"key":"dwa","label":"Dynamic Correction","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 18, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'ASR_XunfeiStream';
INSERT INTO `ai_model_config` VALUES ('ASR_XunfeiStream', 'ASR', 'iFlytek Streaming Speech Recognition', 'iFlytek Streaming Speech Recognition Service', 0, 1, '{"type": "xunfei_stream", "app_id": "", "api_key": "", "api_secret": "", "domain": "slm", "language": "zh_cn", "accent": "mandarin", "dwa": "wpgs", "output_dir": "tmp/"}', 'https://www.xfyun.cn/doc/spark/spark_zh_iat.html', 'Supports real-time streaming speech recognition for Mandarin Chinese and multiple dialects', 21, NULL, NULL, NULL, NULL);

-- Update the documentation of the iFlytek streaming ASR model configuration
UPDATE `ai_model_config` SET
`doc_link` = 'https://www.xfyun.cn/doc/spark/spark_zh_iat.html',
`remark` = 'iFlytek streaming ASR configuration:
1. Log in to the iFlytek Open Platform at https://www.xfyun.cn/
2. Create a speech recognition application to obtain the APPID, APISecret and APIKey
3. Parameters:
   - app_id: application ID, obtained after creating an application on the iFlytek Open Platform
   - api_key: API key used for API authentication
   - api_secret: API key used to generate signatures
   - domain: recognition domain, default slm (intelligent speech transcription)
   - language: recognition language, default zh_cn (Chinese)
   - accent: dialect type, default mandarin, supports cantonese and others
   - dwa: dynamic correction, default wpgs (dynamic correction enabled)
   - output_dir: audio file output directory, default tmp/
4. Supports real-time streaming recognition, suitable for real-time voice interaction scenarios
5. Supports recognition of multiple dialects and languages
' WHERE `id` = 'ASR_XunfeiStream';