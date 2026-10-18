# RAGFlow Integration Guide

This tutorial has two main parts:

- Part 1: How to deploy RAGFlow
- Part 2: How to configure the RAGFlow API in the Control Panel

If you are very familiar with RAGFlow and have already deployed it, you can skip Part 1 and go straight to Part 2. However, if you would like guidance on deploying RAGFlow so that it can share the `mysql` and `redis` infrastructure with `xiaozhi-esp32-server` to reduce resource costs, start from Part 1.

# Part 1 How to Deploy RAGFlow
## Step 1: Check Whether MySQL and Redis Are Available

RAGFlow depends on a `mysql` database. If you have already deployed the `Control Panel`, then `mysql` is already installed, and you can share it.

Try using the `telnet` command on the host to see whether `mysql` port `3306` is reachable.
``` shell
telnet 127.0.0.1 3306

telnet 127.0.0.1 6379
```
If ports `3306` and `6379` are reachable, ignore the rest of this section and go directly to Step 2.

If they are not reachable, think about how your `mysql` was installed.

If `mysql` was installed manually from an installation package, it is likely network-isolated. You may need to resolve access to `mysql` port `3306` first.

If `mysql` was installed through this project's `docker-compose_all.yml`, find the `docker-compose_all.yml` file you used to create the database and change the following content.

Before:
``` yaml
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    expose:
      - "3306:3306"
  xiaozhi-esp32-server-redis:
    ...
    expose:
      - 6379
```

After:
``` yaml
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    ports:
      - "3306:3306"
  xiaozhi-esp32-server-redis:
    ...
    ports:
      - "6379:6379"
```

Note that you change `expose` to `ports` under `xiaozhi-esp32-server-db` and `xiaozhi-esp32-server-redis`. After the change, restart the services. The commands to restart MySQL are:

``` shell
# Go to the folder containing your docker-compose_all.yml, for example xiaozhi-server
cd xiaozhi-server
docker compose -f docker-compose_all.yml down
docker compose -f docker-compose.yml up -d
```

After startup, use the `telnet` command on the host again to see whether `mysql` port `3306` is reachable.
``` shell
telnet 127.0.0.1 3306

telnet 127.0.0.1 6379
```
Normally, it should now be reachable.

## Step 2: Create the Database and Tables
If the host can access the MySQL database normally, create a database named `rag_flow` and a `rag_flow` user with the password `infini_rag_flow`.

``` sql
-- Create the database
CREATE DATABASE IF NOT EXISTS rag_flow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create the user and grant privileges
CREATE USER IF NOT EXISTS 'rag_flow'@'%' IDENTIFIED BY 'infini_rag_flow';
GRANT ALL PRIVILEGES ON rag_flow.* TO 'rag_flow'@'%';

-- Refresh privileges
FLUSH PRIVILEGES;
```

## Step 3: Download the RAGFlow Project

Choose a folder on your computer to store the RAGFlow project, for example `/home/system/xiaozhi`.

You can use the `git` command to download the RAGFlow project into this folder. This tutorial uses version `v0.22.0`.
```
git clone https://ghfast.top/https://github.com/infiniflow/ragflow.git
cd ragflow
git checkout v0.22.0
```
After downloading, enter the `docker` folder.
``` shell
cd docker
```
Edit the `docker-compose.yml` file in the `ragflow/docker` folder and remove the `depends_on` configuration from the `ragflow-cpu` and `ragflow-gpu` services to remove the `ragflow-cpu` service's dependency on `mysql`.

Before:
``` yaml
  ragflow-cpu:
    depends_on:
      mysql:
        condition: service_healthy
    profiles:
      - cpu
  ...
  ragflow-gpu:
    depends_on:
      mysql:
        condition: service_healthy
    profiles:
      - gpu
```
After:
``` yaml
  ragflow-cpu:
    profiles:
      - cpu
  ...
  ragflow-gpu:
    profiles:
      - gpu
```

Next, edit the `docker-compose-base.yml` file in the `ragflow/docker` folder and remove the `mysql` and `redis` configurations.

For example, before deletion:
``` yaml
services:
  minio:
    image: quay.io/minio/minio:RELEASE.2025-06-13T11-33-47Z
    ...
  mysql:
    image: mysql:8.0
    ...
  redis:
    image: redis:6.2-alpine
    ...
```

After deletion:
``` yaml
services:
  minio:
    image: quay.io/minio/minio:RELEASE.2025-06-13T11-33-47Z
    ...
```
## Step 4: Modify the Environment Variable Configuration

Edit the `.env` file in the `ragflow/docker` folder, find the following settings, and change each one individually! Search for each one and change each one!

Regarding the changes to the `.env` file below, 60% of people overlook the `MYSQL_USER` setting and cause RAGFlow to fail to start, so it needs to be emphasized three times:

First emphasis: If your `.env` file does not have a `MYSQL_USER` setting, add it to the configuration file!

Second emphasis: If your `.env` file does not have a `MYSQL_USER` setting, add it to the configuration file!

Third emphasis: If your `.env` file does not have a `MYSQL_USER` setting, add it to the configuration file!

``` env
# Port settings
SVR_WEB_HTTP_PORT=8008           # HTTP port
SVR_WEB_HTTPS_PORT=8009          # HTTPS port
# MySQL configuration - change to your local MySQL information
MYSQL_HOST=host.docker.internal  # Use host.docker.internal so containers can access host services
MYSQL_PORT=3306                  # Local MySQL port
MYSQL_USER=rag_flow              # The username created above; add this entry if it is missing
MYSQL_PASSWORD=infini_rag_flow   # The password set above
MYSQL_DBNAME=rag_flow            # Database name

# Redis configuration - change to your local Redis information
REDIS_HOST=host.docker.internal  # Use host.docker.internal so containers can access host services
REDIS_PORT=6379                  # Local Redis port
REDIS_PASSWORD=                  # If your Redis has no password, leave it like this; otherwise enter the password
```

Note that if your Redis has no password, you also need to edit `service_conf.yaml.template` in the `ragflow/docker` folder and replace `infini_rag_flow` with an empty string.

Before:
``` shell
redis:
  db: 1
  password: '${REDIS_PASSWORD:-infini_rag_flow}'
  host: '${REDIS_HOST:-redis}:6379'
```
After:
``` shell
redis:
  db: 1
  password: '${REDIS_PASSWORD:-}'
  host: '${REDIS_HOST:-redis}:6379'
```

## Step 5: Start the RAGFlow Service
Run:
``` shell
docker-compose -f docker-compose.yml up -d
```
After it succeeds, you can run `docker logs -n 20 -f docker-ragflow-cpu-1` to view the logs of the `docker-ragflow-cpu-1` service.

If there are no errors in the logs, the RAGFlow service started successfully.

# Step 5: Register an Account
Open `http://127.0.0.1:8008` in a browser, click `Sign Up`, and register an account.

After registering, click `Sign In` to log in to RAGFlow. If you want to disable registration so that others cannot create accounts, set `REGISTER_ENABLED` to `0` in the `.env` file in the `ragflow/docker` folder.

``` dotenv
REGISTER_ENABLED=0
```
After the change, restart the RAGFlow service.
``` shell
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml up -d
```

# Step 6: Configure the Models for the RAGFlow Service
Open `http://127.0.0.1:8008` in a browser and click `Sign In` to log in to RAGFlow. Click the `avatar` in the upper-right corner to open the settings page.
First, in the left navigation bar, click `Model providers` to open the model configuration page. Under `Available models` in the right pane, select `LLM`, choose your model provider from the list, click `Add`, and enter your API key.
Then select `TEXT EMBEDDING`, choose your model provider from the list, click `Add`, and enter your API key.
Finally, refresh the page, click LLM and Embedding under `Set default models`, and select the models you use. Make sure your API key has activated the corresponding services. For example, the Embedding model I use is from provider xxx, and you need to check that provider's website to see whether the model requires purchasing a resource package before use.


# Part 2 Configure the RAGFlow Service

# Step 1 Log In to the RAGFlow Service
Open `http://127.0.0.1:8008` in a browser and click `Sign In` to log in to RAGFlow.

Then click the `avatar` in the upper-right corner to open the settings page. In the left navigation bar, click the `API` feature, then click the "API Key" button. A dialog appears.

In the dialog, click "Create new Key" to generate an API key. Copy this `API Key`; you will need it later.

# Step 2 Configure It in the Control Panel
Make sure your Control Panel version is `0.8.7` or later. Log in to the Control Panel with the super administrator account.

First, enable the knowledge base feature. In the top navigation bar, click `Parameter Dictionary`, then click `System Feature Configuration` in the drop-down menu. On the page, check `Knowledge Base` and click `Save Configuration`. The `Knowledge Base` feature will then appear in the navigation bar.

In the top navigation bar, click `Model Configuration`, then click `Knowledge Base` in the left navigation bar. Find `RAG_RAGFlow` in the list and click the `Edit` button.

For `Service Address`, enter `http://your-ragflow-service-lan-ip:8008`. For example, if my RAGFlow service's LAN IP is `192.168.1.100`, I enter `http://192.168.1.100:8008`.

For `API Key`, enter the `API Key` you copied earlier.

Finally, click Save.

# Step 2 Create a Knowledge Base
Log in to the Control Panel with the super administrator account. In the top navigation bar, click `Knowledge Base`, then click the `Add` button in the lower-left corner of the list. Enter a name and description for the knowledge base and click Save.

To improve the LLM's understanding of and recall from the knowledge base, it is recommended to provide a meaningful name and description when creating it. For example, if you are creating a knowledge base about `Company Profile`, the knowledge base name could be `Company Profile`, and the description could be `Relevant company information, such as basic company details, service offerings, contact phone numbers, and address.`.

After saving, the knowledge base appears in the knowledge base list. Click the `View` button for the knowledge base you just created to open its details page.

On the knowledge base details page, click the `Add` button in the lower-left corner to upload documents to the knowledge base.

After uploading, the documents appear on the knowledge base details page. Click the `Parse` button for a document to parse it.

When parsing is complete, you can view the resulting chunks. Click the `Retrieval Test` button on the knowledge base details page to test the knowledge base's recall/retrieval capability.

# Step 3 Let XiaoZhi Use the RAGFlow Knowledge Base
Log in to the Control Panel. In the top navigation bar, click `Agents`, find the agent you want to configure, and click the `Configure Role` button.

To the left of Intent Recognition, click the `Edit Features` button to open a dialog. Select the knowledge base you want to add in the dialog and save.
