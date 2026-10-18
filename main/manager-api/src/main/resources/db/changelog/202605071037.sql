-- Delete the provider with provider_code ttson
DELETE FROM `ai_model_provider` WHERE `provider_code` = 'ttson';

-- Delete the configuration with model_code ACGNTTS
DELETE FROM `ai_model_config` WHERE `model_code` = 'ACGNTTS';
