# FAQ ❓

### 1. Why does XiaoZhi recognize a lot of Korean, Japanese, and English when I speak? 🇰🇷

Suggestion: Check whether `models/SenseVoiceSmall` already contains the `model.pt` file. If not, download it; see [Download the speech recognition model files](Deployment.md#model-files).

### 2. Why do I get "TTS task error: file does not exist"? 📁

Suggestion: Check whether `libopus` and `ffmpeg` were installed correctly with `conda`.

If they are not installed, install them:

```
conda install conda-forge::libopus
conda install conda-forge::ffmpeg
```

### 3. TTS often fails or times out ⏰

Suggestion: If `EdgeTTS` often fails, first check whether you are using a proxy (VPN). If so, try disabling the proxy and test again.
If you are using Volcano Engine's Doubao TTS and it often fails, consider the paid version, because the trial version supports only 2 concurrent requests.

### 4. I can connect to the self-hosted server over Wi-Fi, but not in 4G mode 🔐

Cause: Brother Xia's firmware requires a secure connection in 4G mode.

Solutions: There are currently two options. Choose either one:

1. Modify the code. See this video for a solution: https://www.bilibili.com/video/BV18MfTYoE85

2. Configure an SSL certificate with Nginx. See the tutorial: https://icnt94i5ctj4.feishu.cn/docx/GnYOdMNJOoRCljx1ctecsj9cnRe

### 5. How can I improve XiaoZhi's response speed? ⚡

The default configuration of this project is a low-cost setup. Beginners are advised to start with the default free models to get things "running", then optimize for "speed".
To improve response speed, try switching the individual components. Since version `0.5.2`, the project supports streaming configurations; compared with earlier versions, response speed improves by about `2.5 seconds`, significantly enhancing the user experience.

| Module | Free Starter Setup | Streaming Setup |
|:---:|:---:|:---:|
| ASR (Speech Recognition) | FunASR (local) | 👍XunfeiStreamASR (iFlytek streaming) |
| LLM | glm-4-flash (Zhipu) | 👍qwen-flash (Alibaba Cloud Bailian) |
| VLLM (Vision LLM) | glm-4v-flash (Zhipu) | 👍qwen3.5-flash (Alibaba Cloud Bailian) |
| TTS (Speech Synthesis) | EdgeTTS (Microsoft) | 👍HuoshanDoubleStreamTTS (Volcano Engine streaming) |
| Intent | function_call (function calling) | function_call (function calling) |
| Memory | mem_local_short (local short-term memory) | mem_local_short (local short-term memory) |

If you care about the latency of each component, see the [XiaoZhi component performance test report](https://github.com/xinnan-tech/xiaozhi-performance-research); you can test in your own environment using the methodology described there.

### 6. I speak slowly, but XiaoZhi keeps interrupting during pauses 🗣️

Suggestion: Find the following section in the configuration file and increase the value of `min_silence_duration_ms` (for example, to `1000`):

```yaml
VAD:
  SileroVAD:
    threshold: 0.5
    model_dir: models/snakers4_silero-vad
    min_silence_duration_ms: 700  # Increase this value if you pause for a long time while speaking
```

### 7. Deployment Tutorials
1. [How to perform a minimal deployment](./Deployment.md)<br/>
2. [How to perform a full-module deployment](./Deployment_all.md)<br/>
3. [How to deploy the MQTT gateway and enable the MQTT+UDP protocol](./mqtt-gateway-integration.md)<br/>
4. [How to automatically pull the latest code, build, and start the project](./dev-ops-integration.md)<br/>
5. [How to integrate with Nginx](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791)<br/>
6. [How to build your own Docker image after modifying the code](./docker-build.md)<br/>

### 8. Firmware Compilation Tutorials
1. [How to compile the XiaoZhi firmware yourself](./firmware-build.md)<br/>
2. [How to change the OTA address based on the firmware compiled by Brother Xia](./firmware-setting.md)<br/>
3. [How to configure automatic firmware OTA upgrades for a server-only deployment](./ota-upgrade-guide.md)<br/>

### 9. Extension Tutorials
1. [How to enable phone-number registration for the Control Panel](./ali-sms-integration.md)<br/>
2. [How to integrate Home Assistant for smart home control](./homeassistant-integration.md)<br/>
3. [How to enable vision models for photo-based object recognition](./mcp-vision-integration.md)<br/>
4. [How to deploy an MCP access point](./mcp-endpoint-enable.md)<br/>
5. [How to connect to an MCP access point](./mcp-endpoint-integration.md)<br/>
6. [How to obtain device information through MCP methods](./mcp-get-device-info.md)<br/>
7. [How to enable voiceprint recognition](./voiceprint-integration.md)<br/>
8. [News plugin source configuration guide](./newsnow_plugin_config.md)<br/>
9. [RAGFlow knowledge base integration guide](./ragflow-integration.md)<br/>
10. [How to deploy a context provider](./context-provider-integration.md)<br/>
11. [How to integrate PowerMem intelligent memory](./powermem-integration.md)<br/>
12. [How to configure the weather plugin to query the weather](./weather-integration.md)<br/>
13. [How to enable the device call plugin](./device-call-guide.md)<br/>
14. [How to enable web search](./web-search-integration.md)<br/>

### 10. Digital Human Tutorials
1. [How to start the digital-human module](./digital-human-wakeword.md)<br/>
2. [How to deploy the digital-human module on an N100 mini PC](./all-in-one-digital-human-setup.md)<br/>

### 11. Voice Cloning and Local Voice Deployment Tutorials
1. [How to clone a voice in the Control Panel](./huoshan-streamTTS-voice-cloning.md)<br/>
2. [How to deploy and integrate local index-tts speech](./index-stream-integration.md)<br/>
3. [How to deploy and integrate local fish-speech speech](./fish-speech-integration.md)<br/>
4. [How to deploy and integrate local PaddleSpeech speech](./paddlespeech-deploy.md)<br/>

### 12. Performance Testing Tutorials
1. [Guide to testing the speed of each component](./performance_tester.md)<br/>
2. [Regularly published test results](https://github.com/xinnan-tech/xiaozhi-performance-research)<br/>

### 13. For more questions, contact us 💬

You can submit your questions in [issues](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues).
