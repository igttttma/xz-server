-- VOSK ASR model provider
delete from `ai_model_provider` where id = 'SYSTEM_ASR_VoskASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_VoskASR', 'ASR', 'vosk', 'VOSK Offline Speech Recognition', '[{"key": "model_path", "type": "string", "label": "Model Path"}, {"key": "output_dir", "type": "string", "label": "Output Directory"}]', 11, 1, NOW(), 1, NOW());

-- VOSK ASR model configuration
delete from `ai_model_config` where id = 'ASR_VoskASR';
INSERT INTO `ai_model_config` VALUES ('ASR_VoskASR', 'ASR', 'VoskASR', 'VOSK Offline Speech Recognition', 0, 1, '{\"type\": \"vosk\", \"model_path\": \"\", \"output_dir\": \"tmp/\"}', NULL, NULL, 11, NULL, NULL, NULL, NULL);

-- Update the VOSK ASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://alphacephei.com/vosk/',
`remark` = 'VOSK ASR configuration:
1. VOSK is an offline speech recognition library that supports multiple languages
2. Download the model files first: https://alphacephei.com/vosk/models
3. For Chinese models, vosk-model-small-cn-0.22 or vosk-model-cn-0.22 is recommended
4. Runs fully offline, no network connection required
5. Output files are saved in the tmp/ directory
Usage steps:
1. Visit https://alphacephei.com/vosk/models to download a Chinese model
2. Extract the model files to the models/vosk/ folder under the project directory
3. Specify the correct model path in the configuration
4. Note: the VOSK Chinese model outputs no punctuation, and words are separated by spaces
' WHERE `id` = 'ASR_VoskASR';