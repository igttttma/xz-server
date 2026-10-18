-- LLM intent recognition configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'LLM intent recognition configuration:
1. Uses a dedicated LLM for intent recognition
2. Uses the selected_module.LLM model by default
3. A dedicated LLM can be configured (such as the free ChatGLMLLM)
4. Highly versatile, but increases processing time
Configuration:
1. Specify the LLM model to use in the llm field
2. If not specified, the selected_module.LLM model is used' WHERE `id` = 'Intent_intent_llm';

-- Function call intent recognition configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Function call intent recognition configuration:
1. Uses the function_call feature of the LLM for intent recognition
2. The selected LLM must support function_call
3. Tools are called on demand, resulting in fast processing' WHERE `id` = 'Intent_function_call';