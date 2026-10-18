-- Update the HuoshanDoubleStreamTTS provider configuration, moving scattered parameters into JSON dictionary configuration
-- Consolidate parameters such as speech_rate, loudness_rate, pitch, emotion and emotion_scale into three JSON dictionaries: audio_params, additions and mix_speaker

UPDATE `ai_model_provider`
SET `fields` = '[
  {"key": "ws_url", "type": "string", "label": "WebSocket URL"},
  {"key": "appid", "type": "string", "label": "App ID"},
  {"key": "access_token", "type": "string", "label": "Access Token"},
  {"key": "resource_id", "type": "string", "label": "Resource ID"},
  {"key": "speaker", "type": "string", "label": "Default Voice"},
  {"key": "enable_ws_reuse", "type": "boolean", "label": "Whether to Enable Connection Reuse", "default": true},
  {"key": "audio_params", "type": "dict", "label": "Audio Output Configuration"},
  {"key": "additions", "type": "dict", "label": "Advanced Text Processing Configuration"},
  {"key": "mix_speaker", "type": "dict", "label": "Mixing Control Configuration"}
]'
WHERE `id` = 'SYSTEM_TTS_HSDSTTS';

-- Update existing configurations by migrating the old scattered parameters into the new JSON dictionary structure
UPDATE `ai_model_config`
SET `config_json` = JSON_SET(
    `config_json`,
    '$.audio_params', JSON_OBJECT(
        'speech_rate', CAST(COALESCE(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.speech_rate')), ''), '0') AS SIGNED),
        'loudness_rate', CAST(COALESCE(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.loudness_rate')), ''), '0') AS SIGNED)
    ),
    '$.additions', JSON_OBJECT(
        'aigc_metadata', JSON_OBJECT(),
        'cache_config', JSON_OBJECT(),
        'post_process', JSON_OBJECT(
            'pitch', CAST(COALESCE(NULLIF(JSON_UNQUOTE(JSON_EXTRACT(`config_json`, '$.pitch')), ''), '0') AS SIGNED)
        )
    ),
    '$.mix_speaker', JSON_OBJECT()
)
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';

-- Delete the old scattered parameter fields
UPDATE `ai_model_config`
SET `config_json` = JSON_REMOVE(
    `config_json`,
    '$.speech_rate',
    '$.loudness_rate',
    '$.pitch',
    '$.emotion',
    '$.emotion_scale'
)
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';

-- Update the documentation links and remarks
UPDATE `ai_model_config` SET
`doc_link` = 'https://www.volcengine.com/docs/6561/1329505',
`remark` = 'Volcano Engine bidirectional streaming TTS configuration:
1. Visit https://www.volcengine.com/ to register and activate a Volcano Engine account
2. Visit https://console.volcengine.com/speech/service/10007 to enable the TTS large model and purchase voices
3. Obtain the appid and access_token at the bottom of the page
4. The resource ID is fixed to: volc.service_type.10029 (large model TTS and mixing)
5. Connection reuse: enabling WebSocket connection reuse (default true) reduces connection overhead (note: after reuse, idle connections occupy concurrency while a device is in the listening state)

Detailed parameter documentation: https://www.volcengine.com/docs/6561/1329505
[audio_params] Audio output configuration - users can add any audio parameters supported by Volcano Engine
  - speech_rate: speech rate (-50~100), default 0
  - loudness_rate: volume (-50~100), default 0
  - emotion: emotion type (only some voices support it), options: neutral, happy, sad, angry, fearful, disgusted, surprised
  - emotion_scale: emotion intensity (1~5), default 4
  Example: {"speech_rate": 10, "loudness_rate": 5, "emotion": "happy", "emotion_scale": 4}

[additions] Advanced text processing configuration - users can add any advanced parameters supported by Volcano Engine
  - post_process.pitch: pitch (-12~12), default 0
  - aigc_metadata: AIGC metadata configuration
  - cache_config: cache configuration
  Example: {"post_process": {"pitch": 2}, "aigc_metadata": {}, "cache_config": {}}

[mix_speaker] Mixing control configuration - multi-voice mixing (TTS 1.0 only)
  Example:
    {"speakers": [
      {"source_speaker": "zh_male_bvlazysheep","mix_factor": 0.3}, 
      {"source_speaker": "BV120_streaming","mix_factor": 0.3}, 
      {"source_speaker": "zh_male_ahu_conversation_wvae_bigtts","mix_factor": 0.4}
    ]}

Notes:
- Multi-emotion voice parameters (emotion, emotion_scale) are supported by only some voices
- Voice list: https://www.volcengine.com/docs/6561/1257544
- Users can add more parameters according to the Volcano Engine API documentation
- The mixing feature mainly applies to Doubao TTS Model 1.0 voices; when using it, set req_params.speaker to custom_mix_bigtts
'
WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';
