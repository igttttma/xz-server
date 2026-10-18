-- Delete the configuration with model_code GizwitsTTS
DELETE FROM `ai_model_config` WHERE `model_code` = 'GizwitsTTS';

-- Delete the related TTS voice records
DELETE FROM `ai_tts_voice` WHERE `tts_model_id` = 'TTS_GizwitsTTS';
DELETE FROM `ai_tts_voice` WHERE `tts_model_id` = 'TTS_ACGNTTS';
