-- Add the FunASR service ASR model provider and configuration
DELETE FROM `ai_model_provider` WHERE `id` = 'SYSTEM_ASR_FunASRServer';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_FunASRServer', 'ASR', 'fun_server', 'FunASR Service Speech Recognition', '[{"key":"host","label":"Service Address","type":"string"},{"key":"port","label":"Port","type":"number"}]', 4, 1, NOW(), 1, NOW());

DELETE FROM `ai_model_config` WHERE `id` = 'ASR_FunASRServer';
INSERT INTO `ai_model_config` VALUES ('ASR_FunASRServer', 'ASR', 'FunASRServer', 'FunASR Service Speech Recognition', 0, 1, '{\"type\": \"fun_server\", \"host\": \"127.0.0.1\", \"port\": 10096}', NULL, NULL, 5, NULL, NULL, NULL, NULL);

-- Change the remark column type of the ai_model_config table to TEXT
ALTER TABLE `ai_model_config` MODIFY COLUMN `remark` TEXT COMMENT 'Remark'; 

-- Update the documentation of the ASR model configurations
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = 'Deploying FunASR independently and using the FunASR API service takes only five commands
First: mkdir -p ./funasr-runtime-resources/models
Second: sudo docker run -d -p 10096:10095 --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
After running the previous command you will enter the container; continue with the third: cd FunASR/runtime
Do not exit the container; continue with the fourth inside the container: nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
After running the previous command you will enter the container; continue with the fifth: tail -f log.txt
After the fifth command finishes you will see the model download log; once the download completes you can connect and use it
The above uses CPU inference; if you have a GPU, see: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

-- Update the FunASR local model configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR',
`remark` = 'FunASR local model configuration:
1. Download the model files to the xiaozhi-server/models/SenseVoiceSmall directory
2. Supports Chinese, Japanese, Korean and Cantonese speech recognition
3. Local inference, no network connection required
4. Files to be recognized are saved in the tmp/ directory' WHERE `id` = 'ASR_FunASR';

-- Update the SherpaASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/k2-fsa/sherpa-onnx',
`remark` = 'SherpaASR configuration:
1. Model files are downloaded automatically at runtime to the models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17 directory
2. Supports Chinese, English, Japanese, Korean, Cantonese and other languages
3. Local inference, no network connection required
4. Output files are saved in the tmp/ directory' WHERE `id` = 'ASR_SherpaASR';

-- Update the Doubao ASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = 'Doubao ASR configuration:
1. Create an application in the Volcano Engine console and obtain the appid and access_token
2. Supports Chinese speech recognition
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create a new application
3. Obtain the appid and access_token
4. Fill them into the configuration file' WHERE `id` = 'ASR_DoubaoASR';

-- Update the Tencent ASR configuration documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.cloud.tencent.com/cam/capi',
`remark` = 'Tencent ASR configuration:
1. Create an application in the Tencent Cloud console and obtain the appid, secret_id and secret_key
2. Supports Chinese speech recognition
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://console.cloud.tencent.com/cam/capi to obtain the keys
2. Visit https://console.cloud.tencent.com/asr/resourcebundle to claim free resources
3. Obtain the appid, secret_id and secret_key
4. Fill them into the configuration file' WHERE `id` = 'ASR_TencentASR';

-- Update the TTS model configuration documentation
-- EdgeTTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/rany2/edge-tts',
`remark` = 'EdgeTTS configuration:
1. Uses the Microsoft Edge TTS service
2. Supports multiple languages and voices
3. Free to use, no registration required
4. Network connection required
5. Output files are saved in the tmp/ directory' WHERE `id` = 'TTS_EdgeTTS';

-- Doubao TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/8',
`remark` = 'Doubao TTS configuration:
1. Visit https://console.volcengine.com/speech/service/8
2. Create an application in the Volcano Engine console and obtain the appid and access_token
3. The paid Volcano Engine speech service is required; the starting price is 30 CNY for 100 concurrent connections. The free tier provides only 2 concurrent connections and frequently reports TTS errors
4. After purchasing the service and the free voices, you may need to wait about half an hour before they can be used
5. Fill them into the configuration file' WHERE `id` = 'TTS_DoubaoTTS';

-- SiliconFlow TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.siliconflow.cn/account/ak',
`remark` = 'SiliconFlow TTS configuration:
1. Visit https://cloud.siliconflow.cn/account/ak
2. Register and obtain the API key
3. Fill it into the configuration file' WHERE `id` = 'TTS_CosyVoiceSiliconflow';

-- Coze Chinese TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://www.coze.cn/open/oauth/pats',
`remark` = 'Coze Chinese TTS configuration:
1. Visit https://www.coze.cn/open/oauth/pats
2. Obtain a personal access token
3. Fill it into the configuration file' WHERE `id` = 'TTS_CozeCnTTS';

-- FishSpeech configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/fishaudio/fish-speech',
`remark` = 'FishSpeech configuration:
1. Requires a locally deployed FishSpeech service
2. Supports custom voices
3. Local inference, no network connection required
4. Output files are saved in the tmp/ directory
5. Example command to run the service: python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path "checkpoints/fish-speech-1.5" --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" --decoder-config-name firefly_gan_vq --compile' WHERE `id` = 'TTS_FishSpeech';

-- GPT-SoVITS V2 configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/RVC-Boss/GPT-SoVITS',
`remark` = 'GPT-SoVITS V2 configuration:
1. Requires a locally deployed GPT-SoVITS service
2. Supports custom voice cloning
3. Local inference, no network connection required
4. Output files are saved in the tmp/ directory
Deployment steps:
1. Example command to run the service: python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/demo.yaml' WHERE `id` = 'TTS_GPT_SOVITS_V2';

-- GPT-SoVITS V3 configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/RVC-Boss/GPT-SoVITS',
`remark` = 'GPT-SoVITS V3 configuration:
1. Requires a locally deployed GPT-SoVITS V3 service
2. Supports custom voice cloning
3. Local inference, no network connection required
4. Output files are saved in the tmp/ directory' WHERE `id` = 'TTS_GPT_SOVITS_V3';

-- MiniMax TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.minimaxi.com/',
`remark` = 'MiniMax TTS configuration:
1. Create an account on the MiniMax platform and top up
2. Supports multiple voices; the current configuration uses female-shaonv
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://platform.minimaxi.com/ to register an account
2. Visit https://platform.minimaxi.com/user-center/payment/balance to top up
3. Visit https://platform.minimaxi.com/user-center/basic-information to obtain group_id
4. Visit https://platform.minimaxi.com/user-center/basic-information/interface-key to obtain api_key
5. Fill them into the configuration file' WHERE `id` = 'TTS_MinimaxTTS';

-- Alibaba Cloud TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = 'Alibaba Cloud TTS configuration:
1. Enable the Intelligent Speech Interaction service on the Alibaba Cloud platform
2. Supports multiple voices; the current configuration uses xiaoyun
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://nls-portal.console.aliyun.com/ to enable the service
2. Visit https://nls-portal.console.aliyun.com/applist to obtain the appkey
3. Visit https://nls-portal.console.aliyun.com/overview to obtain the token
4. Fill them into the configuration file
Note: the token is temporary and valid for 24 hours; for long-term use, configure access_key_id and access_key_secret' WHERE `id` = 'TTS_AliyunTTS';

-- Tencent TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.cloud.tencent.com/cam/capi',
`remark` = 'Tencent TTS configuration:
1. Enable the Intelligent Speech Interaction service on the Tencent Cloud platform
2. Supports multiple voices; the current configuration uses 101001
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://console.cloud.tencent.com/cam/capi to obtain the keys
2. Visit https://console.cloud.tencent.com/tts/resourcebundle to claim free resources
3. Create a new application
4. Obtain the appid, secret_id and secret_key
5. Fill them into the configuration file' WHERE `id` = 'TTS_TencentTTS';

-- 302AI TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://dash.302.ai/',
`remark` = '302AI TTS configuration:
1. Create an account on the 302 platform and obtain the API key
2. Supports multiple voices; the current configuration uses the Wanwan Xiaohe voice
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://dash.302.ai/ to register an account
2. Visit https://dash.302.ai/apis/list to obtain the API key
3. Fill it into the configuration file
Price: $35 per million characters' WHERE `id` = 'TTS_TTS302AI';

-- Gizwits TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://agentrouter.gizwitsapi.com/panel/token',
`remark` = 'Gizwits TTS configuration:
1. Obtain an API key on the Gizwits platform
2. Supports multiple voices; the current configuration uses the Wanwan Xiaohe voice
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://agentrouter.gizwitsapi.com/panel/token to obtain the API key
2. Fill it into the configuration file
Note: the first 10,000 registered users receive a 5 CNY trial credit' WHERE `id` = 'TTS_GizwitsTTS';

-- ACGN TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://acgn.ttson.cn/',
`remark` = 'ACGN TTS configuration:
1. Purchase a token on the ttson platform
2. Supports multiple character voices; the current configuration uses character ID: 1695
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://acgn.ttson.cn/ to view the character list
2. Visit www.ttson.cn to purchase a token
3. Fill it into the configuration file
For development-related questions, please use the QQ contact on the website' WHERE `id` = 'TTS_ACGNTTS';

-- OpenAI TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.openai.com/api-keys',
`remark` = 'OpenAI TTS configuration:
1. Obtain an API key on the OpenAI platform
2. Supports multiple voices; the current configuration uses onyx
3. Network connection required
4. Output files are saved in the tmp/ directory
Application steps:
1. Visit https://platform.openai.com/api-keys to obtain the API key
2. Fill it into the configuration file
Note: a proxy is required for access from mainland China' WHERE `id` = 'TTS_OpenAITTS';

-- Custom TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Custom TTS configuration:
1. Supports custom TTS API services
2. Requests use the GET method
3. Network connection required
4. Output files are saved in the tmp/ directory
Configuration:
1. Configure request parameters in params
2. Configure request headers in headers
3. Set the returned audio format' WHERE `id` = 'TTS_CustomTTS';

-- Volcano Engine Edge LLM Gateway TTS configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/vei/aigateway/',
`remark` = 'Volcano Engine Edge LLM Gateway TTS configuration:
1. Visit https://console.volcengine.com/vei/aigateway/
2. Create a gateway access key, search for and select Doubao-TTS
3. If you need to use an LLM, also select Doubao-pro-32k-functioncall
4. Visit https://console.volcengine.com/vei/aigateway/tokens-list to obtain the key
5. Fill it into the configuration file
Voice list reference: https://www.volcengine.com/docs/6561/1257544' WHERE `id` = 'TTS_VolcesAiGatewayTTS';

-- Update the LLM model configuration documentation
-- ChatGLM configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
`remark` = 'ChatGLM configuration:
1. Visit https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. Register and obtain the API key
3. Fill it into the configuration file' WHERE `id` = 'LLM_ChatGLMLLM';

-- Ollama configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://ollama.com/',
`remark` = 'Ollama configuration:
1. Install the Ollama service
2. Run the command: ollama pull qwen2.5
3. Make sure the service is running at http://localhost:11434' WHERE `id` = 'LLM_OllamaLLM';

-- Qwen configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = 'Qwen configuration:
1. Visit https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. Obtain the API key
3. Fill it into the configuration file; the current configuration uses the qwen-turbo model
4. Supports custom parameters: temperature=0.7, max_tokens=500, top_p=1, top_k=50' WHERE `id` = 'LLM_AliLLM';

-- Bailian configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = 'Bailian configuration:
1. Visit https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. Obtain the app_id and api_key
3. Fill them into the configuration file' WHERE `id` = 'LLM_AliAppLLM';

-- Doubao LLM configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement',
`remark` = 'Doubao LLM configuration:
1. Visit https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement
2. Enable the Doubao-1.5-pro service
3. Visit https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey to obtain the API key
4. Fill it into the configuration file
5. The currently recommended model is doubao-1-5-pro-32k-250115
Note: there is a free quota of 500000 tokens' WHERE `id` = 'LLM_DoubaoLLM';

-- DeepSeek configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.deepseek.com/',
`remark` = 'DeepSeek configuration:
1. Visit https://platform.deepseek.com/
2. Register and obtain the API key
3. Fill it into the configuration file' WHERE `id` = 'LLM_DeepSeekLLM';

-- Dify configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.dify.ai/',
`remark` = 'Dify configuration:
1. Visit https://cloud.dify.ai/
2. Register and obtain the API key
3. Fill it into the configuration file
4. Supports multiple conversation modes: workflows/run, chat-messages, completion-messages
5. Role definitions set in the platform do not take effect and must be configured in the Dify console
Note: a locally deployed Dify endpoint is recommended; access to the public cloud endpoint may be restricted in some regions of mainland China' WHERE `id` = 'LLM_DifyLLM';

-- Gemini configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://aistudio.google.com/apikey',
`remark` = 'Gemini configuration:
1. Uses the Google Gemini API service
2. The current configuration uses the gemini-2.0-flash model
3. Network connection required
4. Proxy configuration is supported
Application steps:
1. Visit https://aistudio.google.com/apikey
2. Create an API key
3. Fill it into the configuration file
Note: if used in mainland China, please comply with the Interim Measures for the Management of Generative AI Services' WHERE `id` = 'LLM_GeminiLLM';

-- Coze configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://www.coze.cn/open/oauth/pats',
`remark` = 'Coze configuration:
1. Uses the Coze platform service
2. Requires bot_id, user_id and a personal access token
3. Network connection required
Application steps:
1. Visit https://www.coze.cn/open/oauth/pats
2. Obtain a personal access token
3. Manually calculate bot_id and user_id
4. Fill them into the configuration file' WHERE `id` = 'LLM_CozeLLM';

-- LM Studio configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://lmstudio.ai/',
`remark` = 'LM Studio configuration:
1. Uses a locally deployed LM Studio service
2. The current configuration uses the deepseek-r1-distill-llama-8b@q4_k_m model
3. Local inference, no network connection required
4. The model must be downloaded in advance
Deployment steps:
1. Install LM Studio
2. Download a model from the community
3. Make sure the service is running at http://localhost:1234/v1' WHERE `id` = 'LLM_LMStudioLLM';

-- FastGPT configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.tryfastgpt.ai/account/apikey',
`remark` = 'FastGPT configuration:
1. Uses the FastGPT platform service
2. Network connection required
3. The prompt in the configuration file is ignored and must be set in the FastGPT console
4. Supports custom variables
Application steps:
1. Visit https://cloud.tryfastgpt.ai/account/apikey
2. Obtain the API key
3. Fill it into the configuration file' WHERE `id` = 'LLM_FastgptLLM';

-- Xinference configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xorbitsai/inference',
`remark` = 'Xinference configuration:
1. Uses a locally deployed Xinference service
2. The current configuration uses the qwen2.5:72b-AWQ model
3. Local inference, no network connection required
4. The corresponding model must be started in advance
Deployment steps:
1. Install Xinference
2. Start the service and load the model
3. Make sure the service is running at http://localhost:9997' WHERE `id` = 'LLM_XinferenceLLM';

-- Xinference small model configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xorbitsai/inference',
`remark` = 'Xinference small model configuration:
1. Uses a locally deployed Xinference service
2. The current configuration uses the qwen2.5:3b-AWQ model
3. Local inference, no network connection required
4. Used for intent recognition
Deployment steps:
1. Install Xinference
2. Start the service and load the model
3. Make sure the service is running at http://localhost:9997' WHERE `id` = 'LLM_XinferenceSmallLLM';

-- Volcano Engine Edge LLM Gateway LLM configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/vei/aigateway/',
`remark` = 'Volcano Engine Edge LLM Gateway LLM configuration:
1. Uses the Volcano Engine Edge LLM Gateway service
2. Requires a gateway access key
3. Network connection required
4. Supports the function_call feature
Application steps:
1. Visit https://console.volcengine.com/vei/aigateway/
2. Create a gateway access key, search for and select Doubao-pro-32k-functioncall
3. If you need TTS, also select Doubao-TTS
4. Visit https://console.volcengine.com/vei/aigateway/tokens-list to obtain the key
5. Fill it into the configuration file' WHERE `id` = 'LLM_VolcesAiGatewayLLM';

-- Update the Memory model configuration documentation
-- No-memory configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'No-memory configuration:
1. Does not save conversation history
2. Every conversation is independent
3. No additional configuration required
4. Suitable for scenarios with high privacy requirements' WHERE `id` = 'Memory_nomem';

-- Local short-term memory configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Local short-term memory configuration:
1. Uses local storage to save conversation history
2. Summarizes conversation content through the llm of selected_module
3. Data is stored locally and is not uploaded to the server
4. Suitable for privacy-conscious scenarios
5. No additional configuration required' WHERE `id` = 'Memory_mem_local_short';

-- Mem0AI memory configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://app.mem0.ai/dashboard/api-keys',
`remark` = 'Mem0AI memory configuration:
1. Uses the Mem0AI service to save conversation history
2. Requires an API key
3. Network connection required
4. 1000 free calls per month
Application steps:
1. Visit https://app.mem0.ai/dashboard/api-keys
2. Obtain the API key
3. Fill it into the configuration file' WHERE `id` = 'Memory_mem0ai';

-- Update the Intent model configuration documentation
-- No intent recognition configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'No intent recognition configuration:
1. No intent recognition is performed
2. All conversations are passed directly to the LLM
3. No additional configuration required
4. Suitable for simple conversation scenarios' WHERE `id` = 'Intent_nointent';

-- LLM intent recognition configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'LLM intent recognition configuration:
1. Uses a dedicated LLM for intent recognition
2. Uses the selected_module.LLM model by default
3. A dedicated LLM can be configured (such as the free ChatGLMLLM)
4. Highly versatile, but increases processing time
5. Does not support IoT operations such as volume control
Configuration:
1. Specify the LLM model to use in the llm field
2. If not specified, the selected_module.LLM model is used' WHERE `id` = 'Intent_intent_llm';

-- Function call intent recognition configuration
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'Function call intent recognition configuration:
1. Uses the function_call feature of the LLM for intent recognition
2. The selected LLM must support function_call
3. Tools are called on demand, resulting in fast processing
4. Supports all IoT commands
5. The following functions are loaded by default:
   - handle_exit_intent (exit recognition)
   - play_music (music playback)
   - change_role (role switching)
   - get_weather (weather query)
   - get_news (news query)
Configuration:
1. Configure the function modules to load in the functions field
2. Basic functions are loaded by default and need not be configured again
3. Custom function modules can be added' WHERE `id` = 'Intent_function_call';

-- Update the VAD model configuration documentation
-- SileroVAD configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/snakers4/silero-vad',
`remark` = 'SileroVAD configuration:
1. Uses the SileroVAD model for voice activity detection
2. Local inference, no network connection required
3. The model files must be downloaded to the models/snakers4_silero-vad directory
4. Configurable parameters:
   - threshold: 0.5 (voice detection threshold)
   - min_silence_duration_ms: 700 (minimum silence duration in milliseconds)
5. If pauses in speech are relatively long, the value of min_silence_duration_ms can be increased appropriately' WHERE `id` = 'VAD_SileroVAD';
