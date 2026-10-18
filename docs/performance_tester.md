# Guide to the Performance Testing Tool for ASR, LLMs, Non-Streaming TTS, Streaming TTS, and Vision Models

1. Create a `data` directory under `main/xiaozhi-server`.
2. Create a `.config.yaml` file in the `data` directory.
3. In `.data/config.yaml`, enter the parameters for your ASR, LLM, streaming TTS, and vision models.
For example:
```
LLM:
  ChatGLMLLM:
    # Define the LLM API type
    type: openai
    # glm-4-flash is free, but you still need to register and fill in an api_key
    # You can find your api key at https://bigmodel.cn/usercenter/proj-mgmt/apikeys
    model_name: glm-4-flash
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: your chat-glm web key

TTS:

VLLM:

ASR:
```
4. Run `performance_tester.py` under `main/xiaozhi-server`:
```
python performance_tester.py
```
