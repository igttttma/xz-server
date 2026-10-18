-- Modify parameters from versions before 0.3.0
update `sys_params` set param_value = '.mp3;.wav;.p3' where  param_code = 'plugins.play_music.music_ext';
update `ai_model_config` set config_json =  '{\"type\": \"intent_llm\", \"llm\": \"LLM_ChatGLMLLM\"}' where  id = 'Intent_intent_llm';

-- Add Edge voices
delete from `ai_tts_voice` where tts_model_id = 'TTS_EdgeTTS';
INSERT INTO `ai_tts_voice` VALUES 
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'EdgeTTS Female - Xiaoxiao', 'zh-CN-XiaoxiaoNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'EdgeTTS Male - Yunyang', 'zh-CN-YunyangNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'EdgeTTS Female - Xiaoyi', 'zh-CN-XiaoyiNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'EdgeTTS Male - Yunjian', 'zh-CN-YunjianNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'EdgeTTS Male - Yunxi', 'zh-CN-YunxiNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'EdgeTTS Male - Yunxia', 'zh-CN-YunxiaNeural', 'Mandarin', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'EdgeTTS Female - Liaoning Xiaobei', 'zh-CN-liaoning-XiaobeiNeural', 'Liaoning dialect', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'EdgeTTS Female - Shaanxi Xiaoni', 'zh-CN-shaanxi-XiaoniNeural', 'Shaanxi dialect', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'EdgeTTS Female - Hong Kong HiuGaai', 'zh-HK-HiuGaaiNeural', 'Cantonese', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'EdgeTTS Female - Hong Kong HiuMaan', 'zh-HK-HiuMaanNeural', 'Cantonese', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'EdgeTTS Male - Hong Kong WanLung', 'zh-HK-WanLungNeural', 'Cantonese', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL);

-- Add the parameter controlling whether user registration is allowed
delete from `sys_params` where  id in (103,104);
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (103, 'server.allow_user_register', 'false', 'boolean', 1, 'Whether to allow registration by people other than administrators');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (104, 'server.fronted_url', 'http://xiaozhi.server.com', 'string', 1, 'Control Panel address displayed when sending the six-digit verification code');

-- Fix CosyVoiceSiliconflow voices
delete from `ai_tts_voice` where tts_model_id = 'TTS_CosyVoiceSiliconflow';
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice Male', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Chinese', 'https://example.com/cosyvoice/alex.mp3', NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice Female', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Chinese', 'https://example.com/cosyvoice/bella.mp3', NULL, 6, NULL, NULL, NULL, NULL);
