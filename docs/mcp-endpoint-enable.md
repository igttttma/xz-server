# MCP Access Point Deployment and Usage Guide

This tutorial contains 3 parts:
- 1. How to deploy the MCP access point service
- 2. How to configure the MCP access point for a full-module deployment
- 3. How to configure the MCP access point for a server-only deployment

# 1. How to Deploy the MCP Access Point Service

## Step 1: Download the MCP Access Point Project Source Code

Open the [MCP access point project](https://github.com/xinnan-tech/mcp-endpoint-server) in a browser.

Find the green button labeled `Code` on the page, click it, and you will see a `Download ZIP` button.

Click it to download the source code archive. After downloading, extract it. The extracted folder may be named `mcp-endpoint-server-main`;
rename it to `mcp-endpoint-server`.

## Step 2: Start the Program
This is a simple project, and running it with Docker is recommended. If you prefer not to use Docker, refer to [this page](https://github.com/xinnan-tech/mcp-endpoint-server/blob/main/README_dev.md) to run it from source. The Docker method is below.

```
# Enter the project source root directory
cd mcp-endpoint-server

# Clear the cache
docker compose -f docker-compose.yml down
docker stop mcp-endpoint-server
docker rm mcp-endpoint-server
docker rmi ghcr.nju.edu.cn/xinnan-tech/mcp-endpoint-server:latest

# Start the Docker container
docker compose -f docker-compose.yml up -d
# View the logs
docker logs -f mcp-endpoint-server
```

The logs will contain output similar to the following:
```
250705 INFO-=====The addresses below are the Control Panel and server-only MCP access point addresses====
250705 INFO-Control Panel MCP parameter configuration: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
250705 INFO-Server-only deployment MCP access point: ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
250705 INFO-=====Choose the one that matches your deployment and never disclose it to anyone======
```

Copy the two endpoint addresses:

Because you are deploying with Docker, do not use the addresses above directly!

Because you are deploying with Docker, do not use the addresses above directly!

Because you are deploying with Docker, do not use the addresses above directly!

First copy the addresses into a scratch note. You need to know your computer's LAN IP. For example, if my computer's LAN IP is `192.168.1.25`, then
my original endpoint addresses
```
Control Panel MCP parameter configuration: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
Server-only deployment MCP access point: ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
```
should be changed to
```
Control Panel MCP parameter configuration: http://192.168.1.25:8004/mcp_endpoint/health?key=abc
Server-only deployment MCP access point: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

After changing them, open the `Control Panel MCP parameter configuration` address directly in a browser. If the browser shows something like the following, it worked.
```
{"result":{"status":"success","connections":{"tool_connections":0,"robot_connections":0,"total_connections":0}},"error":null,"id":null,"jsonrpc":"2.0"}
```

Keep both `endpoint addresses` above; you will need them in the next step.

# 2. How to Configure the MCP Access Point for a Full-Module Deployment
First, enable the MCP access point feature. In the Control Panel, click `Parameter Dictionary` at the top, then click `System Feature Configuration` in the drop-down menu. On the page, check `MCP Access Point` and click `Save Configuration`. On the `Role Configuration` page, click the `Edit Features` button and the `MCP Access Point` feature will appear.

If you are using a full-module deployment, log in to the Control Panel with an administrator account, click `Parameter Dictionary` at the top, and select `Parameter Management`.

Then search for the parameter `server.mcp_endpoint`, whose value should currently be `null`.
Click the edit button, paste the `Control Panel MCP parameter configuration` obtained in the previous step into `Parameter Value`, and save.

If it saves successfully, everything went well, and you can check the effect in an agent. If it fails, the Control Panel cannot reach the MCP access point; it is most likely a network firewall issue or an incorrect LAN IP.

# 3. How to Configure the MCP Access Point for a Server-Only Deployment

If you use a server-only deployment, find your configuration file `data/.config.yaml`.
Search the configuration file for `mcp_endpoint`. If it is not found, add the `mcp_endpoint` setting. Mine looks like this:
```
server:
  websocket: ws://your-ip-or-domain:port/xiaozhi/v1/
  http_port: 8002
log:
  log_level: INFO

# There may be more configuration here..

mcp_endpoint: your access point websocket address
```
Now paste the `Server-only deployment MCP access point` obtained in "How to Deploy the MCP Access Point Service" into `mcp_endpoint`. For example:

```
server:
  websocket: ws://your-ip-or-domain:port/xiaozhi/v1/
  http_port: 8002
log:
  log_level: INFO

# There may be more configuration here

mcp_endpoint: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

After configuration, starting the single module produces logs like the following.
```
250705[__main__]-INFO-Initialized component: vad successfully SileroVAD
250705[__main__]-INFO-Initialized component: asr successfully FunASRServer
250705[__main__]-INFO-OTA endpoint is          http://192.168.1.25:8002/xiaozhi/ota/
250705[__main__]-INFO-Vision analysis endpoint is     http://192.168.1.25:8002/mcp/vision/explain
250705[__main__]-INFO-MCP access point is        ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
250705[__main__]-INFO-Websocket address is    ws://192.168.1.25:8000/xiaozhi/v1/
250705[__main__]-INFO-=======The address above is a websocket protocol address; do not open it in a browser=======
250705[__main__]-INFO-To test websocket, start the digital-human module and use the browser interaction test
250705[__main__]-INFO-=============================================================
```

If the output includes the `MCP access point is` line with `ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc`, the configuration succeeded.

