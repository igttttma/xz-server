# Deployment Architecture Diagram
![Please refer to the full-module installation architecture diagram](../docs/images/deploy2.png)
# Method 1: Docker (All Modules)
Starting with version `0.8.2`, the Docker images released for this project support only the `x86 architecture`. If you need to deploy on an `arm64` CPU, you can follow [this tutorial](docker-build.md) to build an `arm64 image` locally.

## 1. Install Docker

If Docker is not installed on your computer, you can follow the tutorial here: [Docker installation](https://www.runoob.com/docker/ubuntu-docker-install.html)

There are two ways to install all modules with Docker: you can [use the quick script](./Deployment_all.md#11-quick-script) (author [@VanillaNahida](https://github.com/VanillaNahida)),
which downloads the required files and configuration automatically, or use [manual deployment](./Deployment_all.md#12-manual-deployment) to build everything from scratch.



### 1.1 Quick Script
For a simpler deployment, see the [video tutorial](https://www.bilibili.com/video/BV17bbvzHExd/). The written tutorial is below:
> [!NOTE]  
> Currently only one-click deployment on Ubuntu servers is supported. Other systems have not been tried and may have unexpected bugs.

Connect to the server with an SSH tool and run the following script as root:
```bash
sudo bash -c "$(wget -qO- https://ghfast.top/https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/docker-setup.sh)"
```

The script automatically performs the following steps:
> 1. Install Docker
> 2. Configure the registry mirror
> 3. Download/pull images
> 4. Download the speech recognition model files
> 5. Guide you through server configuration
>

After the script finishes and you complete the basic configuration, refer to the three most important tasks mentioned in [4. Run the Program](#4-run-the-program) and [5. Restart xiaozhi-esp32-server](#5-restart-xiaozhi-esp32-server). Once these three configurations are complete, the system is ready to use.

### 1.2 Manual Deployment

#### 1.2.1 Create Directories

After installation, choose a directory to hold this project's configuration files. For example, you can create a folder named `xiaozhi-server`.

After creating the directory, create a `data` folder and a `models` folder inside `xiaozhi-server`, and create a `SenseVoiceSmall` folder inside `models`.

The final directory structure looks like this:

```
xiaozhi-server
  ├─ data
  ├─ models
     ├─ SenseVoiceSmall
```

#### 1.2.2 Download the Speech Recognition Model Files

By default, the speech recognition model used by this project is `SenseVoiceSmall` for speech-to-text. Because the model is fairly large, it must be downloaded separately. After downloading, place the `model.pt` file in the `models/SenseVoiceSmall` directory. Use either of the following download sources.

- Source 1: Download [SenseVoiceSmall](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt) from Alibaba ModelScope
- Source 2: Download [SenseVoiceSmall](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) from Baidu Netdisk. Extraction code:
  `qvna`


#### 1.2.3 Download the Configuration Files

You need to download two configuration files: `docker-compose_all.yaml` and `config_from_api.yaml`. Download them from the project repository.

##### 1.2.3.1 Download docker-compose_all.yaml

Open [this link](../main/xiaozhi-server/docker-compose_all.yml) in a browser.

On the right side of the page, find the button labeled `RAW`. Next to the `RAW` button, find the download icon and click it to download the `docker-compose_all.yml` file. Download the file into your `xiaozhi-server` directory.

Alternatively, download it directly with `wget https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/refs/heads/main/main/xiaozhi-server/docker-compose_all.yml`.

After downloading, return to this tutorial and continue.

##### 1.2.3.2 Download config_from_api.yaml

Open [this link](../main/xiaozhi-server/config_from_api.yaml) in a browser.

On the right side of the page, find the button labeled `RAW`. Next to the `RAW` button, find the download icon and click it to download the `config_from_api.yaml` file. Download the file into the `data` folder under `xiaozhi-server`, then rename `config_from_api.yaml` to `.config.yaml`.

Alternatively, download it directly with `wget https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/refs/heads/main/main/xiaozhi-server/config_from_api.yaml`.

After downloading the configuration files, confirm that the contents of `xiaozhi-server` look like this:

```
xiaozhi-server
  ├─ docker-compose_all.yml
  ├─ data
    ├─ .config.yaml
  ├─ models
     ├─ SenseVoiceSmall
       ├─ model.pt
```

If your directory structure matches the above, continue. If not, check carefully whether you missed a step.

## 2. Back Up Data

If you have successfully run the Control Panel before and it contains your secret information, copy the important data from the Control Panel first. The upgrade process may overwrite the existing data.

## 3. Remove Old Images and Containers
Next, open a command-line tool, go to your `xiaozhi-server` directory using `Terminal` or `Command Prompt`, and run the following commands:

```
docker compose -f docker-compose_all.yml down

docker stop xiaozhi-esp32-server
docker rm xiaozhi-esp32-server

docker stop xiaozhi-esp32-server-web
docker rm xiaozhi-esp32-server-web

docker stop xiaozhi-esp32-server-db
docker rm xiaozhi-esp32-server-db

docker stop xiaozhi-esp32-server-redis
docker rm xiaozhi-esp32-server-redis

docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest
```

## 4. Run the Program
Run the following command to start the new version's containers:

```
docker compose -f docker-compose_all.yml up -d
```

After it finishes, run the following command to view the logs.

```
docker logs -f xiaozhi-esp32-server-web
```

When you see log output like this, the `Control Panel` has started successfully.

```
2025-xx-xx 22:11:12.445 [main] INFO  c.a.d.s.b.a.DruidDataSourceAutoConfigure - Init DruidDataSource
2025-xx-xx 21:28:53.873 [main] INFO  xiaozhi.AdminApplication - Started AdminApplication in 16.057 seconds (process running for 17.941)
http://localhost:8002/xiaozhi/doc.html
```

Note that at this point only the `Control Panel` is running. If port 8000 reports errors from `xiaozhi-esp32-server`, ignore them for now.

Now use a browser to open the `Control Panel` at http://127.0.0.1:8002 and register the first user. The first user becomes the super administrator; all later users are regular users. Regular users can only bind devices and configure agents, while the super administrator can manage models and users and edit parameters.

Next, complete three important tasks:

### First Important Task

Log in to the Control Panel with the super administrator account, find `Parameter Management` in the top menu, and locate the first entry in the list. Its parameter code is `server.secret`; copy its `Parameter Value`.

A note about `server.secret`: this `parameter value` is important because it lets the `Server` connect to `manager-api`. `server.secret` is a secret generated randomly each time the manager module is deployed from scratch.

After copying the `parameter value`, open the `.config.yaml` file in the `data` directory under `xiaozhi-server`. At this point your configuration file should look like this:

```
manager-api:
  url:  http://127.0.0.1:8002/xiaozhi
  secret: your server.secret value
```
1. Copy the `server.secret` `parameter value` you just copied from the `Control Panel` into the `secret` field of the `.config.yaml` file.

2. Since you are deploying with Docker, change `url` to `http://xiaozhi-esp32-server-web:8002/xiaozhi` below.

3. Since you are deploying with Docker, change `url` to `http://xiaozhi-esp32-server-web:8002/xiaozhi` below.

4. Since you are deploying with Docker, change `url` to `http://xiaozhi-esp32-server-web:8002/xiaozhi` below.

The result should look like this:
```
manager-api:
  url: http://xiaozhi-esp32-server-web:8002/xiaozhi
  secret: 12345678-xxxx-xxxx-xxxx-123456789000
```

After saving, continue with the second important task.

### Second Important Task

Log in to the Control Panel with the super administrator account, find `Model Configuration` in the top menu, click `Large Language Model` in the left sidebar, locate the first entry `Zhipu AI`, and click the `Edit` button.
In the dialog that appears, enter the API key you obtained for `Zhipu AI` into `API Key`, then click Save.

## 5. Restart xiaozhi-esp32-server

Next, open a command-line tool using `Terminal` or `Command Prompt` and run:

```
docker restart xiaozhi-esp32-server
docker logs -f xiaozhi-esp32-server
```
If you see logs similar to the following, the server has started successfully.

```
25-02-23 12:01:09[core.websocket_server] - INFO - Websocket address is      ws://xxx.xx.xx.xx:8000/xiaozhi/v1/
25-02-23 12:01:09[core.websocket_server] - INFO - =======The address above is a websocket protocol address; do not open it in a browser=======
25-02-23 12:01:09[core.websocket_server] - INFO - To test websocket, start the digital-human module and use the browser interaction test
25-02-23 12:01:09[core.websocket_server] - INFO - =======================================================
```

Because you are doing a full-module deployment, there are two important endpoints to enter into the ESP32.

OTA endpoint:
```
http://your-host-lan-ip:8002/xiaozhi/ota/
```

WebSocket endpoint:
```
ws://your-host-ip:8000/xiaozhi/v1/
```

### Third Important Task

Log in to the Control Panel with the super administrator account, find `Parameter Management` in the top menu, locate the parameter code `server.websocket`, and enter your `WebSocket endpoint`.

Log in to the Control Panel with the super administrator account, find `Parameter Management` in the top menu, locate the parameter code `server.ota`, and enter your `OTA endpoint`.

Next, you can start working with your ESP32 device. You can either `compile the ESP32 firmware yourself` or use `the firmware version 1.6.1 or later compiled by Brother Xia`. Choose either one.

1. [Compile your own ESP32 firmware](firmware-build.md).

2. [Configure a custom server based on the firmware compiled by Brother Xia](firmware-setting.md).


# Method 2: Local Source Code (All Modules)

## 1. Install the MySQL Database

If MySQL is already installed on your machine, you can create a database named `xiaozhi_esp32_server` directly.

```sql
CREATE DATABASE xiaozhi_esp32_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

If MySQL is not installed yet, you can install it with Docker:

```
docker run --name xiaozhi-esp32-server-db -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -e MYSQL_DATABASE=xiaozhi_esp32_server -e MYSQL_INITDB_ARGS="--character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci" -e TZ=Asia/Shanghai -d mysql:latest
```

## 2. Install Redis

If Redis is not installed yet, you can install it with Docker:

```
docker run --name xiaozhi-esp32-server-redis -d -p 6379:6379 redis
```

## 3. Run the manager-api Program

3.1 Install JDK 21 and set the JDK environment variables.

3.2 Install Maven and set the Maven environment variables.

3.3 Install the Java-related extensions for the VS Code editor.

3.4 Load the manager-api module in VS Code.

Configure the database connection in `src/main/resources/application-dev.yml`:

```
spring:
  datasource:
    username: root
    password: 123456
```
Configure the Redis connection in `src/main/resources/application-dev.yml`:
```
spring:
    data:
      redis:
        host: localhost
        port: 6379
        password:
        database: 0
```

3.5 Run the main program.

This project is a Spring Boot application. To start it, open `Application.java` and run the `Main` method.

```
File path:
src/main/java/xiaozhi/AdminApplication.java
```

When you see log output like this, `manager-api` has started successfully.

```
2025-xx-xx 22:11:12.445 [main] INFO  c.a.d.s.b.a.DruidDataSourceAutoConfigure - Init DruidDataSource
2025-xx-xx 21:28:53.873 [main] INFO  xiaozhi.AdminApplication - Started AdminApplication in 16.057 seconds (process running for 17.941)
http://localhost:8002/xiaozhi/doc.html
```

## 4. Run the manager-web Program

4.1 Install Node.js.

4.2 Load the manager-web module in VS Code.

From a terminal, go to the manager-web directory:

```
npm install
```
Then start it:
```
npm run serve
```

Note that if your manager-api endpoints are not at `http://localhost:8002`, change the path in `main/manager-web/.env.development` while developing.

After it starts successfully, use a browser to open the `Control Panel` at http://127.0.0.1:8001 and register the first user. The first user becomes the super administrator; all later users are regular users. Regular users can only bind devices and configure agents, while the super administrator can manage models and users and edit parameters.


Important: After registering, log in to the Control Panel with the super administrator account, find `Model Configuration` in the top menu, click `Large Language Model` in the left sidebar, locate the first entry `Zhipu AI`, and click the `Edit` button.
In the dialog that appears, enter the API key you obtained for `Zhipu AI` into `API Key`, then click Save.

Important: After registering, log in to the Control Panel with the super administrator account, find `Model Configuration` in the top menu, click `Large Language Model` in the left sidebar, locate the first entry `Zhipu AI`, and click the `Edit` button.
In the dialog that appears, enter the API key you obtained for `Zhipu AI` into `API Key`, then click Save.

Important: After registering, log in to the Control Panel with the super administrator account, find `Model Configuration` in the top menu, click `Large Language Model` in the left sidebar, locate the first entry `Zhipu AI`, and click the `Edit` button.
In the dialog that appears, enter the API key you obtained for `Zhipu AI` into `API Key`, then click Save.

## 5. Install the Python Environment

This project uses `conda` to manage its dependency environment. If installing `conda` is inconvenient, install `libopus` and `ffmpeg` for your operating system instead.
If you decide to use `conda`, install it first and then run the following commands.

Important: Windows users can install `Anaconda` to manage the environment. After installing `Anaconda`, search for `anaconda` in the Start menu,
find `Anaconda Prompt`, and run it as administrator, as shown below.

![conda_prompt](./images/conda_env_1.png)

After launching it, if you see `(base)` at the beginning of the command prompt, you have successfully entered the `conda` environment and can run the following commands.

![conda_env](./images/conda_env_2.png)

```
conda remove -n xiaozhi-esp32-server --all -y
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server

# Add the Tsinghua mirror channel
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge

conda install libopus -y
conda install ffmpeg -y

# When deploying on Linux, if you encounter an error about a missing libiconv.so.2 shared library, install it with the following command
conda install libiconv -y
```

Note that these commands will not all succeed if run in one go. Run them step by step and check the output after each step to confirm success.

## 6. Install the Project Dependencies

First, download the project source code. You can use the `git clone` command if you are familiar with it.

Otherwise, open this URL in a browser: `https://github.com/xinnan-tech/xiaozhi-esp32-server.git`

Find the green button labeled `Code` on the page, click it, and you will see a `Download ZIP` button.

Click it to download the source code archive. After downloading, extract it. The extracted folder may be named `xiaozhi-esp32-server-main`;
rename it to `xiaozhi-esp32-server`. Inside it, go into the `main` folder and then into `xiaozhi-server`. Remember this `xiaozhi-server` directory.

```
# Continue using the conda environment
conda activate xiaozhi-esp32-server
# Go to your project root directory, then into main/xiaozhi-server
cd main/xiaozhi-server
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt
```

### 7. Download the Speech Recognition Model Files

By default, the speech recognition model used by this project is `SenseVoiceSmall` for speech-to-text. Because the model is fairly large, it must be downloaded separately. After downloading, place the `model.pt` file in the `models/SenseVoiceSmall` directory. Use either of the following download sources.

- Source 1: Download [SenseVoiceSmall](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt) from Alibaba ModelScope
- Source 2: Download [SenseVoiceSmall](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) from Baidu Netdisk. Extraction code:
  `qvna`

## 8. Configure the Project Files

Log in to the Control Panel with the super administrator account, find `Parameter Management` in the top menu, and locate the first entry in the list. Its parameter code is `server.secret`; copy its `Parameter Value`.

A note about `server.secret`: this `parameter value` is important because it lets the `Server` connect to `manager-api`. `server.secret` is a secret generated randomly each time the manager module is deployed from scratch.

If your `xiaozhi-server` directory has no `data` directory, create one.
If there is no `.config.yaml` under `data`, copy `config_from_api.yaml` from the `xiaozhi-server` directory to `data` and rename it to `.config.yaml`.

After copying the `parameter value`, open the `.config.yaml` file in the `data` directory under `xiaozhi-server`. At this point your configuration file should look like this:

```
manager-api:
  url: http://127.0.0.1:8002/xiaozhi
  secret: your server.secret value
```

Copy the `server.secret` `parameter value` you just copied from the `Control Panel` into the `secret` field of the `.config.yaml` file.

The result should look like this:
```
manager-api:
  url: http://127.0.0.1:8002/xiaozhi
  secret: 12345678-xxxx-xxxx-xxxx-123456789000
```

## 9. Run the Project

```
# Make sure you run this in the xiaozhi-server directory
conda activate xiaozhi-esp32-server
python app.py
```

If you see logs similar to the following, the project service has started successfully.

```
25-02-23 12:01:09[core.websocket_server] - INFO - Server is running at ws://xxx.xx.xx.xx:8000/xiaozhi/v1/
25-02-23 12:01:09[core.websocket_server] - INFO - =======The address above is a websocket protocol address; do not open it in a browser=======
25-02-23 12:01:09[core.websocket_server] - INFO - To test websocket, start the digital-human module and use the browser interaction test
25-02-23 12:01:09[core.websocket_server] - INFO - =======================================================
```

Because you are doing a full-module deployment, there are two important endpoints.

OTA endpoint:
```
http://your-computer-lan-ip:8002/xiaozhi/ota/
```

WebSocket endpoint:
```
ws://your-computer-lan-ip:8000/xiaozhi/v1/
```

Be sure to enter both endpoint addresses into the Control Panel: they affect WebSocket address delivery and the automatic upgrade feature.

1. Log in to the Control Panel with the super administrator account, find `Parameter Management` in the top menu, locate the parameter code `server.websocket`, and enter your `WebSocket endpoint`.

2. Log in to the Control Panel with the super administrator account, find `Parameter Management` in the top menu, locate the parameter code `server.ota`, and enter your `OTA endpoint`.


Next, you can start working with your ESP32 device. You can either `compile the ESP32 firmware yourself` or use `the firmware version 1.6.1 or later compiled by Brother Xia`. Choose either one.

1. [Compile your own ESP32 firmware](firmware-build.md).

2. [Configure a custom server based on the firmware compiled by Brother Xia](firmware-setting.md).

# FAQ
Here are some common questions for reference:

1. [Why does XiaoZhi recognize a lot of Korean, Japanese, and English when I speak?](./FAQ.md)<br/>
2. [Why do I get "TTS task error: file does not exist"?](./FAQ.md)<br/>
3. [TTS often fails or times out](./FAQ.md)<br/>
4. [I can connect to the self-hosted server over Wi-Fi, but not in 4G mode](./FAQ.md)<br/>
5. [How can I improve XiaoZhi's response speed?](./FAQ.md)<br/>
6. [I speak slowly, but XiaoZhi keeps interrupting during pauses](./FAQ.md)<br/>
## Deployment Tutorials
1. [How to automatically pull the latest code, build, and start the project](./dev-ops-integration.md)<br/>
2. [How to deploy the MQTT gateway and enable the MQTT+UDP protocol](./mqtt-gateway-integration.md)<br/>
3. [How to integrate with Nginx](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791)<br/>
## Extension Tutorials
1. [How to enable phone-number registration for the Control Panel](./ali-sms-integration.md)<br/>
2. [How to integrate Home Assistant for smart home control](./homeassistant-integration.md)<br/>
3. [How to enable vision models for photo-based object recognition](./mcp-vision-integration.md)<br/>
4. [How to deploy an MCP access point](./mcp-endpoint-enable.md)<br/>
5. [How to connect to an MCP access point](./mcp-endpoint-integration.md)<br/>
6. [How to enable voiceprint recognition](./voiceprint-integration.md)<br/>
7. [News plugin source configuration guide](./newsnow_plugin_config.md)<br/>
8. [Weather plugin usage guide](./weather-integration.md)<br/>
## Voice Cloning and Local Voice Deployment Tutorials
1. [How to clone a voice in the Control Panel](./huoshan-streamTTS-voice-cloning.md)<br/>
2. [How to deploy and integrate local index-tts speech](./index-stream-integration.md)<br/>
3. [How to deploy and integrate local fish-speech speech](./fish-speech-integration.md)<br/>
4. [How to deploy and integrate local PaddleSpeech speech](./paddlespeech-deploy.md)<br/>
## Performance Testing Tutorials
1. [Guide to testing the speed of each component](./performance_tester.md)<br/>
2. [Regularly published test results](https://github.com/xinnan-tech/xiaozhi-performance-research)<br/>
