# Voiceprint Recognition Setup Guide

This tutorial contains 3 parts:
- 1. How to deploy the voiceprint recognition service
- 2. How to configure the voiceprint API for a full-module deployment
- 3. How to configure voiceprint recognition for a minimal deployment

# 1. How to Deploy the Voiceprint Recognition Service

## Step 1: Download the Voiceprint Recognition Project Source Code

Open the [voiceprint recognition project](https://github.com/xinnan-tech/voiceprint-api) in a browser.

Find the green button labeled `Code` on the page, click it, and you will see a `Download ZIP` button.

Click it to download the source code archive. After downloading, extract it. The extracted folder may be named `voiceprint-api-main`;
rename it to `voiceprint-api`.

## Step 2: Create the Database and Tables

Voiceprint recognition depends on a `mysql` database. If you have already deployed the `Control Panel`, then `mysql` is already installed, and you can share it.

Try using the `telnet` command on the host to see whether `mysql` port `3306` is reachable.
```
telnet 127.0.0.1 3306
```
If port 3306 is reachable, ignore the rest of this section and go directly to Step 3.

If it is not reachable, think about how your `mysql` was installed.

If `mysql` was installed manually from an installation package, it is likely network-isolated. You may need to resolve access to `mysql` port `3306` first.

If `mysql` was installed through this project's `docker-compose_all.yml`, find the `docker-compose_all.yml` file you used to create the database and change the following content.

Before:
```
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    expose:
      - "3306:3306"
```

After:
```
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    ports:
      - "3306:3306"
```

Note that you change `expose` to `ports` under `xiaozhi-esp32-server-db`. After the change, restart the services. The commands to restart MySQL are:

```
# Go to the folder containing your docker-compose_all.yml, for example xiaozhi-server
cd xiaozhi-server
docker compose -f docker-compose_all.yml down
docker compose -f docker-compose.yml up -d
```

After startup, use the `telnet` command on the host again to see whether `mysql` port `3306` is reachable.
```
telnet 127.0.0.1 3306
```
Normally, it should now be reachable.

## Step 3: Create the Database and Tables
If the host can access the MySQL database normally, create a database named `voiceprint_db` and a table named `voiceprints` in MySQL.

```
CREATE DATABASE voiceprint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE voiceprint_db;

CREATE TABLE voiceprints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    speaker_id VARCHAR(255) NOT NULL UNIQUE,
    feature_vector LONGBLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_speaker_id (speaker_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Step 4: Configure the Database Connection

Enter the `voiceprint-api` folder and create a folder named `data`.

Copy `voiceprint.yaml` from the root of `voiceprint-api` into the `data` folder and rename it to `.voiceprint.yaml`.

Next, you need to configure the database connection in `.voiceprint.yaml` carefully.

```
mysql:
  host: "127.0.0.1"
  port: 3306
  user: "root"
  password: "your_password"
  database: "voiceprint_db"
```

Note! Because your voiceprint recognition service is deployed with Docker, `host` must be set to the LAN IP of the machine where `mysql` runs.

Note! Because your voiceprint recognition service is deployed with Docker, `host` must be set to the LAN IP of the machine where `mysql` runs.

Note! Because your voiceprint recognition service is deployed with Docker, `host` must be set to the LAN IP of the machine where `mysql` runs.

## Step 5: Start the Program
This is a simple project, and running it with Docker is recommended. If you prefer not to use Docker, refer to [this page](https://github.com/xinnan-tech/voiceprint-api/blob/main/README.md) to run it from source. The Docker method is below.

```
# Enter the project source root directory
cd voiceprint-api

# Clear the cache
docker compose -f docker-compose.yml down
docker stop voiceprint-api
docker rm voiceprint-api
docker rmi ghcr.nju.edu.cn/xinnan-tech/voiceprint-api:latest

# Start the Docker container
docker compose -f docker-compose.yml up -d
# View the logs
docker logs -f voiceprint-api
```

The logs will contain output similar to the following:
```
250711 INFO-🚀 Starting: production environment service (Uvicorn), listening on: 0.0.0.0:8005
250711 INFO-============================================================
250711 INFO-Voiceprint API URL: http://127.0.0.1:8005/voiceprint/health?key=abcd
250711 INFO-============================================================
```

Copy the voiceprint API URL:

Because you are deploying with Docker, do not use the address above directly!

Because you are deploying with Docker, do not use the address above directly!

Because you are deploying with Docker, do not use the address above directly!

First copy the address into a scratch note. You need to know your computer's LAN IP. For example, if my computer's LAN IP is `192.168.1.25`, then
my original API address
```
http://127.0.0.1:8005/voiceprint/health?key=abcd

```
should be changed to
```
http://192.168.1.25:8005/voiceprint/health?key=abcd
```

After changing it, open the `voiceprint API URL` directly in a browser. If the browser shows something like the following, it worked.
```
{"total_voiceprints":0,"status":"healthy"}
```

Keep the modified `voiceprint API URL`; you will need it in the next step.

# 2. How to Configure Voiceprint Recognition for a Full-Module Deployment

## Step 1 Configure the API
First, enable voiceprint recognition. In the Control Panel, click `Parameter Dictionary` at the top, then click `System Feature Configuration` in the drop-down menu. On the page, check `Voiceprint Recognition` and click `Save Configuration`. The `Voiceprint Recognition` button will then appear on the agent creation card.

If you are using a full-module deployment, log in to the Control Panel with an administrator account, click `Parameter Dictionary` at the top, and select `Parameter Management`.

Then search for the parameter `server.voice_print`, whose value should currently be `null`.
Click the edit button, paste the `voiceprint API URL` obtained in the previous step into `Parameter Value`, and save.

If it saves successfully, everything went well, and you can check the effect in an agent. If it fails, the Control Panel cannot reach voiceprint recognition; it is most likely a network firewall issue or an incorrect LAN IP.

## Step 2 Set the Agent Memory Mode

Open your agent's role configuration and set Memory to `Local short-term memory`. Be sure to enable `Report text + speech`.

## Step 3 Chat with Your Agent

Power on your device and chat with it at a normal speaking rate and pitch.

## Step 4 Set Up Voiceprints

In the Control Panel, on the `Agent Management` page, each agent card has a `Voiceprint Recognition` button; click it. At the bottom there is an `Add` button, which lets you enroll the voiceprint of a person's speech.
In the dialog, it is recommended to fill in the `Description` field with the person's occupation, personality, and hobbies, so the agent can analyze and understand the speaker.

## Step 3 Chat with Your Agent

Power on your device and ask it, "Do you know who I am?" If it can answer, voiceprint recognition is working.

# 3. How to Configure Voiceprint Recognition for a Minimal Deployment

## Step 1 Configure the API
Open the `xiaozhi-server/data/.config.yaml` file (create it if it does not exist), then add or modify the following:

```
# Voiceprint recognition configuration
voiceprint:
  # Voiceprint API URL
  url: your voiceprint API URL
  # Speaker configuration: speaker_id,name,description
  speakers:
    - "test1,Zhang San,Zhang San is a programmer"
    - "test2,Li Si,Li Si is a product manager"
    - "test3,Wang Wu,Wang Wu is a designer"
```

Paste the `voiceprint API URL` obtained in the previous step into `url`, then save.

Add entries to the `speakers` parameter as needed. Note the `speaker_id` parameter, which will be used later when enrolling voiceprints.

## Step 2 Enroll Voiceprints
If you have started the voiceprint service, open `http://localhost:8005/voiceprint/docs` in a local browser to view the API documentation. Here we only explain how to use the voiceprint enrollment API.

The voiceprint enrollment API is `http://localhost:8005/voiceprint/register`, using the POST method.

The request header must include Bearer Token authentication. The token is the part after `?key=` in the `voiceprint API URL`. For example, if my voiceprint registration address is `http://127.0.0.1:8005/voiceprint/health?key=abcd`, my token is `abcd`.

The request body contains the speaker ID (`speaker_id`) and a WAV audio file (`file`). Example request:

```
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "speaker_id=your_speaker_id_here" \
  -F "file=@/path/to/your/file" \
  http://localhost:8005/voiceprint/register
```

 The `file` here is the audio file of the speaker whose voiceprint is being enrolled. The `speaker_id` must match the `speaker_id` configured in the API setup in step 1. For example, if I want to enroll Zhang San's voiceprint and Zhang San's `speaker_id` in `.config.yaml` is `test1`, then when enrolling Zhang San's voiceprint, the `speaker_id` in the request body is `test1`, and `file` is an audio file of Zhang San speaking.

 ## Step 3 Start the Services

Start the XiaoZhi server and the voiceprint service, and it is ready to use.
