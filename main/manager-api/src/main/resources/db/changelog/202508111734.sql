-- Update the HuoshanDoubleStreamTTS provider and add speech rate, pitch and other settings
UPDATE `ai_model_provider`
SET fields = '[{"key": "ws_url", "type": "string", "label": "WebSocket URL"}, {"key": "appid", "type": "string", "label": "App ID"}, {"key": "access_token", "type": "string", "label": "Access Token"}, {"key": "resource_id", "type": "string", "label": "Resource ID"}, {"key": "speaker", "type": "string", "label": "Default Voice"}, {"key": "speech_rate", "type": "number", "label": "Speech Rate (-50~100)"}, {"key": "loudness_rate", "type": "number", "label": "Volume (-50~100)"}, {"key": "pitch", "type": "number", "label": "Pitch (-12~12)"}]'
WHERE id = 'SYSTEM_TTS_HSDSTTS';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/10007',
`remark` = 'Volcano Engine TTS service configuration:
1. Visit https://www.volcengine.com/ to register and activate a Volcano Engine account
2. Visit https://console.volcengine.com/speech/service/10007 to enable the TTS large model and purchase voices
3. Obtain the appid and access_token at the bottom of the page
5. The resource ID is fixed to: volc.service_type.10029 (large model TTS and mixing)
6. Speech rate: -50~100, optional, default 0
7. Volume: -50~100, optional, default 0
8. Pitch: -12~12, optional, default 0
9. Fill them into the configuration file' WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';