-- Delete unused model providers
delete from `ai_model_provider` where id = 'SYSTEM_LLM_doubao';
delete from `ai_model_provider` where id = 'SYSTEM_LLM_chatglm';
delete from `ai_model_provider` where id = 'SYSTEM_TTS_302ai';
delete from `ai_model_provider` where id = 'SYSTEM_TTS_gizwits';

-- Add a model provider
delete from `ai_model_provider` where id = 'SYSTEM_ASR_TencentASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_TencentASR', 'ASR', 'tencent', 'Tencent Speech Recognition', '[{"key":"appid","label":"App ID","type":"string"},{"key":"secret_id","label":"Secret ID","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 4, 1, NOW(), 1, NOW());

-- Add the Tencent TTS model provider
delete from `ai_model_provider` where id = 'SYSTEM_TTS_TencentTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_TencentTTS', 'TTS', 'tencent', 'Tencent TTS', '[{"key":"appid","label":"App ID","type":"string"},{"key":"secret_id","label":"Secret ID","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"region","label":"Region","type":"string"},{"key":"voice","label":"Voice ID","type":"string"}]', 5, 1, NOW(), 1, NOW());


-- Add Edge voices
delete from `ai_tts_voice` where id in ('TTS_EdgeTTS0001', 'TTS_EdgeTTS0002', 'TTS_EdgeTTS0003', 'TTS_EdgeTTS0004', 'TTS_EdgeTTS0005', 'TTS_EdgeTTS0006', 'TTS_EdgeTTS0007', 'TTS_EdgeTTS0008', 'TTS_EdgeTTS0009', 'TTS_EdgeTTS0010', 'TTS_EdgeTTS0011');
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

-- DoubaoTTS voices
delete from `ai_tts_voice` where id in ('TTS_DoubaoTTS0001', 'TTS_DoubaoTTS0002', 'TTS_DoubaoTTS0003', 'TTS_DoubaoTTS0004', 'TTS_DoubaoTTS0005');
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0001', 'TTS_DoubaoTTS', 'Standard Female', 'BV001_streaming', 'Mandarin', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV001.mp3', NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0002', 'TTS_DoubaoTTS', 'Standard Male', 'BV002_streaming', 'Mandarin', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV002.mp3', NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0003', 'TTS_DoubaoTTS', 'Sunny Male', 'BV056_streaming', 'Mandarin', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV056.mp3', NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0004', 'TTS_DoubaoTTS', 'Cute Child', 'BV051_streaming', 'Mandarin', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV051.mp3', NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0005', 'TTS_DoubaoTTS', 'Wanwan Xiaohe', 'zh_female_wanwanxiaohe_moon_bigtts', 'Mandarin', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 6, NULL, NULL, NULL, NULL);

-- Fix CosyVoiceSiliconflow voices
delete from `ai_tts_voice` where id in ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow0002');
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice Male', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Chinese', NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice Female', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Chinese', NULL, NULL, 6, NULL, NULL, NULL, NULL);

-- CozeCnTTS voices
delete from `ai_tts_voice` where id = 'TTS_CozeCnTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_CozeCnTTS0001', 'TTS_CozeCnTTS', 'CozeCn Voice', '7426720361733046281', 'Chinese', NULL, NULL, 7, NULL, NULL, NULL, NULL);

-- MinimaxTTS voices
delete from `ai_tts_voice` where id = 'TTS_MinimaxTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxTTS0001', 'TTS_MinimaxTTS', 'Minimax Young Female', 'female-shaonv', 'Chinese', NULL, NULL, 8, NULL, NULL, NULL, NULL);

-- AliyunTTS voices
delete from `ai_tts_voice` where id = 'TTS_AliyunTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunTTS0001', 'TTS_AliyunTTS', 'Alibaba Cloud Xiaoyun', 'xiaoyun', 'Chinese', NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- TTS302AI voices
delete from `ai_tts_voice` where id = 'TTS_TTS302AI0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_TTS302AI0001', 'TTS_TTS302AI', 'Wanwan Xiaohe', 'zh_female_wanwanxiaohe_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 10, NULL, NULL, NULL, NULL);

-- GizwitsTTS voices
delete from `ai_tts_voice` where id = 'TTS_GizwitsTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_GizwitsTTS0001', 'TTS_GizwitsTTS', 'Gizwits Wanwan', 'zh_female_wanwanxiaohe_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 11, NULL, NULL, NULL, NULL);

-- ACGNTTS voices
delete from `ai_tts_voice` where id = 'TTS_ACGNTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_ACGNTTS0001', 'TTS_ACGNTTS', 'ACGN Voice', '1695', 'Chinese', NULL, NULL, 12, NULL, NULL, NULL, NULL);

-- OpenAITTS voices
delete from `ai_tts_voice` where id = 'TTS_OpenAITTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_OpenAITTS0001', 'TTS_OpenAITTS', 'OpenAI Male', 'onyx', 'Chinese', NULL, NULL, 13, NULL, NULL, NULL, NULL);

-- Add Tencent TTS voices
delete from `ai_tts_voice` where id = 'TTS_TencentTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_TencentTTS0001', 'TTS_TencentTTS', 'Zhiyu', '101001', 'Chinese', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- Other voices
delete from `ai_tts_voice` where id = 'TTS_FishSpeech0000';
INSERT INTO `ai_tts_voice` VALUES ('TTS_FishSpeech0000', 'TTS_FishSpeech', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);

delete from `ai_tts_voice` where id = 'TTS_GPT_SOVITS_V20000';
INSERT INTO `ai_tts_voice` VALUES ('TTS_GPT_SOVITS_V20000', 'TTS_GPT_SOVITS_V2', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);

delete from `ai_tts_voice` where id in ('TTS_GPT_SOVITS_V30000', 'TTS_CustomTTS0000');
INSERT INTO `ai_tts_voice` VALUES ('TTS_GPT_SOVITS_V30000', 'TTS_GPT_SOVITS_V3', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CustomTTS0000', 'TTS_CustomTTS', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);

