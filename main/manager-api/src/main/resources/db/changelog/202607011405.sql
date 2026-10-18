-- Add language configuration for local FunASR ASR.
UPDATE `ai_model_provider`
SET `fields` = '[{"key":"model_dir","label":"Model Directory","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"language","label":"Recognition Language","type":"string","default":"auto"}]'
WHERE `id` = 'SYSTEM_ASR_FunASR';

UPDATE `ai_model_config`
SET `config_json` = JSON_SET(`config_json`, '$.language', 'auto')
WHERE `id` = 'ASR_FunASR'
AND JSON_EXTRACT(`config_json`, '$.language') IS NULL;

-- Update the FunASR local model configuration description to mention the language option.
UPDATE `ai_model_config`
SET `remark` = 'FunASR local model configuration:
1. Download the model files to the xiaozhi-server/models/SenseVoiceSmall directory
2. Supports Chinese, Japanese, Korean and Cantonese speech recognition
3. Local inference, no network connection required
4. Files to be recognized are saved in the tmp/ directory
5. The "Recognition Language" field controls the recognition language: auto = automatic detection; to restrict recognition to Chinese, set it to zh (en=English, ja=Japanese, ko=Korean, yue=Cantonese).'
WHERE `id` = 'ASR_FunASR';
