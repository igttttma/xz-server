-- VLLM model configuration
delete from `ai_model_config` where id = 'VLLM_QwenVLVLLM';
INSERT INTO `ai_model_config` VALUES ('VLLM_QwenVLVLLM', 'VLLM', 'QwenVLVLLM', 'Qwen Vision Model', 0, 1, '{\"type\": \"openai\", \"model_name\": \"qwen2.5-vl-3b-instruct\", \"base_url\": \"https://dashscope.aliyuncs.com/compatible-mode/v1\", \"api_key\": \"your_api_key\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);

-- Update the documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2845564.html&renderType=iframe',
`remark` = 'Qwen Vision Model configuration:
1. Visit https://bailian.console.aliyun.com/?tab=model#/api-key
2. Register and obtain the API key
3. Fill it into the configuration file' WHERE `id` = 'VLLM_QwenVLVLLM';

-- Delete the parameters; these two have been moved to the Python configuration file
delete from `sys_params` where id  in (113,114);
