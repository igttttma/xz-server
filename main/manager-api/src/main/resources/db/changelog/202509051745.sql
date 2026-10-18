-- Add the MinimaxHTTPStream streaming TTS provider
delete from `ai_model_provider` where id = 'SYSTEM_TTS_MinimaxStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_MinimaxStreamTTS', 'TTS', 'minimax_httpstream', 'Minimax Streaming TTS', '[{"key":"group_id","label":"Group ID","type":"string"},{"key":"api_key","label":"API Key","type":"string"},{"key":"model","label":"Model","type":"string"},{"key":"voice_id","label":"Voice ID","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"voice_setting","label":"Voice Settings","type":"dict","dict_name":"voice_setting"},{"key":"pronunciation_dict","label":"Pronunciation Dictionary","type":"dict","dict_name":"pronunciation_dict"},{"key":"audio_setting","label":"Audio Settings","type":"dict","dict_name":"audio_setting"},{"key":"timber_weights","label":"Voice Weight","type":"string"}]', 18, 1, NOW(), 1, NOW());

-- Add the Minimax streaming TTS model configuration
delete from `ai_model_config` where id = 'TTS_MinimaxStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_MinimaxStreamTTS', 'TTS', 'MinimaxStreamTTS', 'Minimax Streaming TTS', 0, 1, '{"type": "minimax_httpstream", "group_id": "", "api_key": "", "model": "speech-01-turbo", "voice_id": "female-shaonv", "output_dir": "tmp/", "voice_setting": {"speed": 1, "vol": 1, "pitch": 0, "emotion": "happy"}, "pronunciation_dict": {"tone": []}, "audio_setting": {"sample_rate": 24000, "bitrate": 128000, "format": "pcm", "channel": 1}}', NULL, NULL, 21, NULL, NULL, NULL, NULL);

-- Update the Minimax streaming TTS configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.minimaxi.com/',
`remark` = 'Minimax streaming TTS configuration:
1. Apply for a Minimax API key first
2. Group ID is required
3. Supports multiple voice settings and audio parameter adjustments
4. Supports real-time streaming synthesis with low latency
5. Supports custom pronunciation dictionaries and voice weights
6. Advanced parameter configuration: voice settings (voice_setting), pronunciation dictionary (pronunciation_dict), voice weights (timber_weights)
   - speed: range [0.5,2], default 1.0; higher values make speech faster
   - vol: range (0,10], default 1.0; higher values make volume louder
   - pitch: range [-12,12], default 0; must be an integer
   - emotion: controls the emotion of synthesized speech; supports 7 values: ["happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm"]; this parameter only applies to speech-2.5-hd-preview, speech-2.5-turbo-preview, speech-02-hd, speech-02-turbo, speech-01-turbo and speech-01-hd
   - Either timbre_weights or voice_id is required
   - voice_id (requested voice ID; must be provided together with the weight parameter)
   - weight (weight; supports mixing up to 4 voices; range [1,100])
' WHERE `id` = 'TTS_MinimaxStreamTTS';

-- Add Minimax streaming TTS voices
delete from `ai_tts_voice` where tts_model_id = 'TTS_MinimaxStreamTTS';

-- Default voice
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0001', 'TTS_MinimaxStreamTTS', 'Young Girl Voice', 'female-shaonv', 'Chinese', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0002', 'TTS_MinimaxStreamTTS', 'Mature Female', 'female-chengshu', 'Chinese', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0003', 'TTS_MinimaxStreamTTS', 'Overbearing Young Master', 'badao_shaoye', 'Chinese', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0004', 'TTS_MinimaxStreamTTS', 'Yandere Younger Brother', 'bingjiao_didi', 'Chinese', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0005', 'TTS_MinimaxStreamTTS', 'Innocent Junior', 'chunzhen_xuedi', 'Chinese', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0006', 'TTS_MinimaxStreamTTS', 'Aloof Senior', 'lengdan_xiongzhang', 'Chinese', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0007', 'TTS_MinimaxStreamTTS', 'Sweet Xiaoling', 'tianxin_xiaoling', 'Chinese', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0008', 'TTS_MinimaxStreamTTS', 'Playful Cute Girl', 'qiaopi_mengmei', 'Chinese', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0009', 'TTS_MinimaxStreamTTS', 'Charming Mature Woman', 'wumei_yujie', 'Chinese', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0010', 'TTS_MinimaxStreamTTS', 'Sweet Junior', 'diadia_xuemei', 'Chinese', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0011', 'TTS_MinimaxStreamTTS', 'Elegant Senior', 'danya_xuejie', 'Chinese', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0012', 'TTS_MinimaxStreamTTS', 'Santa Claus', 'Santa_Claus', 'Chinese', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxStreamTTS_0013', 'TTS_MinimaxStreamTTS', 'Grinch', 'Grinch', 'Chinese', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
