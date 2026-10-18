# Vision Model Usage Guide
This tutorial is divided into two parts:
- Part 1: Enabling the vision model when running xiaozhi-server as a single module
- Part 2: Enabling the vision model in a full-module deployment

Before enabling the vision model, prepare three things:
- A device with a camera whose camera invocation feature has already been implemented in Brother Xia's repository, for example the `LCSC Shizhanpai ESP32-S3 development board`.
- Device firmware upgraded to version 1.6.6 or later.
- The basic conversation module is already working.

## Enabling the Vision Model When Running xiaozhi-server as a Single Module

### Step 1 Check the Network
The vision model starts port 8003 by default.

If you run with Docker, check whether your `docker-compose.yml` exposes port `8003`. If not, update to the latest `docker-compose.yml` file.

If you run from source, make sure the firewall allows port `8003`.

### Step 2 Choose Your Vision Model
Open your `data/.config.yaml` file and set `selected_module.VLLM` to a vision model. We currently support vision models with `openai`-compatible APIs. `ChatGLMVLLM` is one such OpenAI-compatible model.

```
selected_module:
  VAD: ..
  ASR: ..
  LLM: ..
  VLLM: ChatGLMVLLM
  TTS: ..
  Memory: ..
  Intent: ..
```

Suppose we use `ChatGLMVLLM` as the vision model. We first need to log in to the [Zhipu AI](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) website and apply for a key. If you have already applied for a key, you can reuse it.

Add this configuration to your configuration file; if it already exists, set your api_key.

```
VLLM:
  ChatGLMVLLM:
    api_key: your api_key
```

### Step 3 Start the xiaozhi-server Service
If you run from source, start it with:
```
python app.py
```
If you run with Docker, restart the container:
```
docker restart xiaozhi-esp32-server
```

After startup, the logs will contain output like the following.

```
2025-06-01 **** - OTA endpoint is           http://192.168.4.7:8003/xiaozhi/ota/
2025-06-01 **** - Vision analysis endpoint is        http://192.168.4.7:8003/mcp/vision/explain
2025-06-01 **** - Websocket address is       ws://192.168.4.7:8000/xiaozhi/v1/
2025-06-01 **** - =======The address above is a websocket protocol address; do not open it in a browser=======
2025-06-01 **** - To test websocket, start the digital-human module and use the browser interaction test
2025-06-01 **** - =============================================================
```

After startup, open the `vision analysis endpoint` from the logs in a browser. What does it output? If you are on Linux and have no browser, run:
```
curl -i your vision analysis endpoint
```

Normally it displays:
```
The MCP Vision API is running normally. The vision explanation endpoint is: http://xxxx:8003/mcp/vision/explain
```

Note that if you deploy on the public internet or with Docker, you must change this setting in `data/.config.yaml`:
```
server:
  vision_explain: http://your-ip-or-domain:port/mcp/vision/explain
```

Why? Because the vision explanation endpoint is sent to the device. If the address is a LAN address or an internal Docker address, the device cannot access it.

Suppose your public address is `111.111.111.111`; then `vision_explain` should be configured as:

```
server:
  vision_explain: http://111.111.111.111:8003/mcp/vision/explain
```

If the MCP Vision API is running normally and the delivered `vision explanation endpoint address` opens correctly in your browser, continue to the next step.

### Step 4 Enable It by Waking the Device

Say to the device, "Please turn on the camera and tell me what you see."

Watch the xiaozhi-server logs for errors.


## Enabling the Vision Model in a Full-Module Deployment

### Step 1 Check the Network
The vision model starts port 8003 by default.

If you run with Docker, check whether your `docker-compose_all.yml` maps port `8003`. If not, update to the latest `docker-compose_all.yml` file.

If you run from source, make sure the firewall allows port `8003`.

### Step 2 Check Your Configuration File

Open your `data/.config.yaml` file and check whether its structure matches `data/config_from_api.yaml`. If it differs or is missing items, fill them in.

### Step 3 Configure the Vision Model Key

Log in to the [Zhipu AI](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) website and apply for a key. If you have already applied for a key, you can reuse it.

Log in to the `Control Panel`, click `Model Configuration` in the top menu, click `Vision Large Language Models` in the left sidebar, find `VLLM_ChatGLMVLLM`, and click the edit button. In the dialog, enter your key in `API Key` and click Save.

After saving successfully, go to the agent you want to test, click `Configure Role`, and check whether `Vision Large Language Model (VLLM)` is set to the vision model you just configured. Click Save.

### Step 3 Start the xiaozhi-server Module
If you run from source, start it with:
```
python app.py
```
If you run with Docker, restart the container:
```
docker restart xiaozhi-esp32-server
```

After startup, the logs will contain output like the following.

```
2025-06-01 **** - Vision analysis endpoint is        http://192.168.4.7:8003/mcp/vision/explain
2025-06-01 **** - Websocket address is       ws://192.168.4.7:8000/xiaozhi/v1/
2025-06-01 **** - =======The address above is a websocket protocol address; do not open it in a browser=======
2025-06-01 **** - To test websocket, start the digital-human module and use the browser interaction test
2025-06-01 **** - =============================================================
```

After startup, open the `vision analysis endpoint` from the logs in a browser. What does it output? If you are on Linux and have no browser, run:
```
curl -i your vision analysis endpoint
```

Normally it displays:
```
The MCP Vision API is running normally. The vision explanation endpoint is: http://xxxx:8003/mcp/vision/explain
```

Note that if you deploy on the public internet or with Docker, you must change this setting in `data/.config.yaml`:
```
server:
  vision_explain: http://your-ip-or-domain:port/mcp/vision/explain
```

Why? Because the vision explanation endpoint is sent to the device. If the address is a LAN address or an internal Docker address, the device cannot access it.

Suppose your public address is `111.111.111.111`; then `vision_explain` should be configured as:

```
server:
  vision_explain: http://111.111.111.111:8003/mcp/vision/explain
```

If the MCP Vision API is running normally and the delivered `vision explanation endpoint address` opens correctly in your browser, continue to the next step.

### Step 4 Enable It by Waking the Device

Say to the device, "Please turn on the camera and tell me what you see."

Watch the xiaozhi-server logs for errors.
