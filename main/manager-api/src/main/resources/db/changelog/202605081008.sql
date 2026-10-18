-- Delete the provider configuration with provider_code linkerai
DELETE FROM `ai_model_provider` WHERE `provider_code` = 'linkerai';

-- Delete the model configuration with model_code LinkeraiTTS
DELETE FROM `ai_model_config` WHERE `model_code` = 'LinkeraiTTS';

-- Delete the TTS voice records related to LinkeraiTTS
DELETE FROM `ai_tts_voice` WHERE `tts_model_id` = 'TTS_LinkeraiTTS';
