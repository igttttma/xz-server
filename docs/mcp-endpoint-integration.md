# MCP Access Point Usage Guide

This tutorial uses the open-source MCP calculator from Brother Xia as an example to show how to connect your own custom MCP service to your access point.

This tutorial assumes that the MCP access point feature is already enabled for your `xiaozhi-server`. If not, enable it by following [this tutorial](./mcp-endpoint-enable.md).

# How to Connect a Simple MCP Feature, Such as a Calculator, to an Agent

### If You Use a Full-Module Deployment
If you use a full-module deployment, open the Control Panel, go to Agent Management, and click `Configure Role`. To the right of `Intent Recognition` there is an `Edit Features` button.

Click that button. On the page that opens, at the bottom, you will see `MCP Access Point`. Normally it shows the agent's `MCP Access Point Address`. Next, let us extend this agent with a calculator feature based on MCP.

This `MCP Access Point Address` is important; you will need it shortly.

### If You Use a Server-Only Deployment
If you use a server-only deployment and have configured the MCP access point address in the configuration file, starting the single module normally produces logs like the following.
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

As shown, the address printed after `MCP access point is`, `ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc`, is your `MCP Access Point Address`.

This `MCP Access Point Address` is important; you will need it shortly.

## Step 1 Download Brother Xia's MCP Calculator Project

Open Brother Xia's [calculator project](https://github.com/78/mcp-calculator) in a browser.

Find the green button labeled `Code` on the page, click it, and you will see a `Download ZIP` button.

Click it to download the source code archive. After downloading, extract it. The extracted folder may be named `mcp-calculator-main`;
rename it to `mcp-calculator`. Next, use the command line to enter the project directory and install the dependencies.


```bash
# Enter the project directory
cd mcp-calculator

conda remove -n mcp-calculator --all -y
conda create -n mcp-calculator python=3.10 -y
conda activate mcp-calculator

pip install -r requirements.txt
```

## Step 2 Start It

Before starting, copy the MCP access point address from your Control Panel agent.

For example, my agent's MCP address is:
```
ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

Run the command:

```bash
export MCP_ENDPOINT=ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

Then start the program:

```bash
python mcp_pipe.py calculator.py
```

### If You Use a Control Panel Deployment
If you use a Control Panel deployment, after starting, go back to the Control Panel and refresh the MCP connection status; you will see the list of features you extended.

### If You Use a Server-Only Deployment
If you use a server-only deployment, logs like the following appear after the device connects, indicating success:

```
250705 -INFO-Initializing MCP access point: wss://2662r3426b.vicp.fun/mcp_e 
250705 -INFO-Sending MCP access point initialization message
250705 -INFO-MCP access point connected successfully
250705 -INFO-MCP access point initialized successfully
250705 -INFO-Unified tool handler initialized
250705 -INFO-MCP access point server info: name=Calculator, version=1.9.4
250705 -INFO-Number of tools supported by the MCP access point: 1
250705 -INFO-All MCP access point tools retrieved; client is ready
250705 -INFO-Tool cache refreshed
250705 -INFO-Currently supported function list: [ 'get_time', 'get_lunar', 'play_music', 'get_weather', 'handle_exit_intent', 'calculator']
```
If it includes `'calculator'`, the device can invoke the calculator tool based on intent recognition.
