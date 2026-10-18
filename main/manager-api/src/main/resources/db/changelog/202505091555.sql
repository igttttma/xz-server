-- Update the model provider table
UPDATE `ai_model_provider` SET fields = '[{"key": "host", "type": "string", "label": "Service Address"}, {"key": "port", "type": "number", "label": "Port"}, {"key": "type", "type": "string", "label": "Service Type"}, {"key": "is_ssl", "type": "boolean", "label": "Whether to Use SSL"}, {"key": "api_key", "type": "string", "label": "API Key"}, {"key": "output_dir", "type": "string", "label": "Output Directory"}]' WHERE id = 'SYSTEM_ASR_FunASRServer';

-- Update the model configuration table
UPDATE `ai_model_config` SET 
config_json = '{"host": "127.0.0.1", "port": 10096, "type": "fun_server", "is_ssl": true, "api_key": "none", "output_dir": "tmp/"}',
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = 'Deploying FunASR independently and using the FunASR API service takes only five commands
First: mkdir -p ./funasr-runtime-resources/models
Second: sudo docker run -p 10096:10095 -it --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
After running the previous command you will enter the container; continue with the third: cd FunASR/runtime
Do not exit the container; continue with the fourth inside the container: nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
After running the previous command you will enter the container; continue with the fifth: tail -f log.txt
After the fifth command finishes you will see the model download log; once the download completes you can connect and use it
The above uses CPU inference; if you have a GPU, see: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

-- FishSpeech configuration
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md',
`remark` = 'FishSpeech configuration:
1. Requires a locally deployed FishSpeech service
2. Supports custom voices
3. Local inference, no network connection required
4. Output files are saved in the tmp/ directory
5. See the tutorial at https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md' WHERE `id` = 'TTS_FishSpeech';
