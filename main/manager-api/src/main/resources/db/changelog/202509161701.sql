-- Add the Alibaba Bailian streaming TTS provider
delete from `ai_model_provider` where id = 'SYSTEM_TTS_AliBLStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_AliBLStreamTTS', 'TTS', 'alibl_stream', 'Alibaba Bailian Streaming TTS', '[{"key":"api_key","label":"API Key","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"model","label":"Model","type":"string"},{"key":"voice","label":"Voice","type":"string"},{"key":"format","label":"Audio Format","type":"string"},{"key":"sample_rate","label":"Sample Rate","type":"number"},{"key": "volume", "type": "number", "label": "Volume"},{"key": "rate", "type": "number", "label": "Speech Rate"},{"key": "pitch", "type": "number", "label": "Pitch"}]', 19, 1, NOW(), 1, NOW());

-- Add the Alibaba Bailian streaming TTS model configuration
delete from `ai_model_config` where id = 'TTS_AliBLStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_AliBLStreamTTS', 'TTS', 'AliBLStreamTTS', 'Alibaba Bailian Streaming TTS', 0, 1, '{\"type\": \"alibl_stream\", \"appkey\": \"\", \"output_dir\": \"tmp/\", \"model\": \"cosyvoice-v2\", \"voice\": \"longcheng_v2\", \"format\": \"pcm\", \"sample_rate\": 24000, \"volume\": 50, \"rate\": 1, \"pitch\": 1}', NULL, NULL, 22, NULL, NULL, NULL, NULL);

-- Update the Alibaba Bailian streaming TTS configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = 'Alibaba Bailian streaming TTS:
1. Visit https://bailian.console.aliyun.com/?apiKey=1#/api-key to create a project and obtain the appkey
2. Supports real-time streaming synthesis with low latency
3. Supports multiple voice settings and audio parameter adjustments
4. Supports CosyVoice-V3 large model voices at an affordable price (0.4 CNY per 10,000 characters)
5. Supports real-time adjustment of volume, speech rate, pitch and other parameters
6. To use the CosyVoice-V3 model and some restricted voice types, contact Alibaba Bailian customer service to apply
' WHERE `id` = 'TTS_AliBLStreamTTS';

-- Add Alibaba Bailian streaming TTS voices
delete from `ai_tts_voice` where tts_model_id = 'TTS_AliBLStreamTTS';

-- Voice assistant
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0001', 'TTS_AliBLStreamTTS', 'Long Xiaochun - Intellectual Positive Female', 'longxiaochun_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0002', 'TTS_AliBLStreamTTS', 'Long Xiaoxia - Calm Authoritative Female', 'longxiaoxia_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);

-- Live commerce
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0003', 'TTS_AliBLStreamTTS', 'Long Anran - Lively Textured Female', 'longanran', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0004', 'TTS_AliBLStreamTTS', 'Long Anxuan - Classic Livestream Female', 'longanxuan', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);

-- Social companionship
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0005', 'TTS_AliBLStreamTTS', 'Long Han - Warm Devoted Male', 'longhan_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0006', 'TTS_AliBLStreamTTS', 'Long Yan - Warm Spring Breeze Female', 'longyan_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0007', 'TTS_AliBLStreamTTS', 'Long Feifei - Sweet Affected Female', 'longfeifei_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);

-- Dialect
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0008', 'TTS_AliBLStreamTTS', 'Long Laotie - Northeast Candid Male', 'longlaotie_v2', 'Chinese (Northeast) and mixed Chinese-English', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0009', 'TTS_AliBLStreamTTS', 'Long Jiayi - Intellectual Cantonese Female', 'longjiayi_v2', 'Chinese (Cantonese) and mixed Chinese-English', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- Child voice
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0010', 'TTS_AliBLStreamTTS', 'Long Jielidou - Sunny Playful Male', 'longjielidou_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0011', 'TTS_AliBLStreamTTS', 'Long Ling - Childish Rigid Female', 'longling_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 11, NULL, NULL, NULL, NULL);

-- Poetry recitation
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0012', 'TTS_AliBLStreamTTS', 'Li Bai - Ancient Poet Immortal Male', 'libai_v2', 'Chinese and mixed Chinese-English', NULL, NULL, NULL, NULL, 12, NULL, NULL, NULL, NULL);

-- Overseas marketing
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0013', 'TTS_AliBLStreamTTS', 'loongeva - Intellectual English Female', 'loongeva_v2', 'British English', NULL, NULL, NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0014', 'TTS_AliBLStreamTTS', 'loongbrian - Calm English Male', 'loongbrian_v2', 'British English', NULL, NULL, NULL, NULL, 14, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0015', 'TTS_AliBLStreamTTS', 'loongkyong - Korean Female', 'loongkyong_v2', 'Korean', NULL, NULL, NULL, NULL, 15, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0016', 'TTS_AliBLStreamTTS', 'loongtomoka - Japanese Female', 'loongtomoka_v2', 'Japanese', NULL, NULL, NULL, NULL, 16, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliBLStreamTTS_0017', 'TTS_AliBLStreamTTS', 'loongtomoya - Japanese Male', 'loongtomoya_v2', 'Japanese', NULL, NULL, NULL, NULL, 17, NULL, NULL, NULL, NULL);