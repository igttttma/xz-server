-- Alibaba Bailian streaming TTS business space WebSocket URL support

UPDATE `ai_model_provider`
SET `fields` = JSON_ARRAY(
    JSON_OBJECT('key', 'api_key', 'type', 'string', 'label', 'API Key'),
    JSON_OBJECT(
        'key', 'ws_url',
        'type', 'string',
        'label', 'WebSocket URL (with Workspace ID)',
        'default', 'wss://dashscope.aliyuncs.com/api-ws/v1/inference/'
    ),
    JSON_OBJECT('key', 'output_dir', 'type', 'string', 'label', 'Output Directory'),
    JSON_OBJECT('key', 'model', 'type', 'string', 'label', 'Model'),
    JSON_OBJECT('key', 'voice', 'type', 'string', 'label', 'Voice'),
    JSON_OBJECT('key', 'format', 'type', 'string', 'label', 'Audio Format'),
    JSON_OBJECT('key', 'sample_rate', 'type', 'number', 'label', 'Sample Rate'),
    JSON_OBJECT('key', 'volume', 'type', 'number', 'label', 'Volume'),
    JSON_OBJECT('key', 'rate', 'type', 'number', 'label', 'Speech Rate'),
    JSON_OBJECT('key', 'pitch', 'type', 'number', 'label', 'Pitch')
)
WHERE `id` = 'SYSTEM_TTS_AliBLStreamTTS';

UPDATE `ai_model_config`
SET `config_json` = JSON_SET(
    `config_json`,
    '$.ws_url',
    COALESCE(
        NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.ws_url')), ''),
        'wss://dashscope.aliyuncs.com/api-ws/v1/inference/'
    )
)
WHERE `id` = 'TTS_AliBLStreamTTS';

UPDATE `ai_model_config`
SET `remark` = 'Alibaba Bailian streaming TTS configuration:
1. Set API Key to a DashScope API key available in the current business space
2. In public mode, use wss://dashscope.aliyuncs.com/api-ws/v1/inference/
3. For the North China 2 (Beijing) business space, use wss://<WorkspaceId>.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference
4. For the Singapore business space, use wss://<WorkspaceId>.ap-southeast-1.maas.aliyuncs.com/api-ws/v1/inference
5. Replace <WorkspaceId> with the real business space ID; only official Alibaba Cloud WSS inference endpoints are supported
6. Supports CosyVoice streaming synthesis and volume, speech rate and pitch configuration'
WHERE `id` = 'TTS_AliBLStreamTTS';
