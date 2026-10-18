# MQTT Gateway Deployment Tutorial

The `xiaozhi-esp32-server` project can be lightly adapted to work with Brother Xia's open-source [xiaozhi-mqtt-gateway](https://github.com/78/xiaozhi-mqtt-gateway) project to enable MQTT+UDP connections for XiaoZhi hardware.
This tutorial has three parts. Choose the part that matches your full-module or server-only deployment:
- Part 1: Deploy the MQTT gateway
- Part 2: Full-module deployment with MQTT+UDP connections for XiaoZhi hardware
- Part 3: Running xiaozhi-server as a single module with MQTT+UDP connections for XiaoZhi hardware

## Preparation
Prepare the `mqtt-websocket` connection address for your `xiaozhi-server`. Append `?from=mqtt_gateway` to your existing `websocket address` to get the `mqtt-websocket` connection address.

1. If you deploy from source, your `mqtt-websocket` address is:
```
ws://127.0.0.1:8000/xiaozhi/v1/?from=mqtt_gateway
```

2. If you deploy with Docker, your `mqtt-websocket` address is:
```
ws://your-host-lan-IP:8000/xiaozhi/v1/?from=mqtt_gateway
```

## Important Notes

If you deploy on a server, make sure ports `1883`, `8884`, and `8007` are open to the outside. The protocol type for `8884` is `UDP`; the others use `TCP`.

If you deploy on a server, make sure ports `1883`, `8884`, and `8007` are open to the outside. The protocol type for `8884` is `UDP`; the others use `TCP`.

If you deploy on a server, make sure ports `1883`, `8884`, and `8007` are open to the outside. The protocol type for `8884` is `UDP`; the others use `TCP`.


## Part 1: Deploy the MQTT Gateway

1. Clone the [adapted xiaozhi-mqtt-gateway project](https://github.com/xinnan-tech/xiaozhi-mqtt-gateway.git):
```bash
git clone https://ghfast.top/https://github.com/xinnan-tech/xiaozhi-mqtt-gateway.git
cd xiaozhi-mqtt-gateway
```

2. Install dependencies:
```bash
npm install
npm install -g pm2
```

3. Configure `config.json`:
```bash
cp config/mqtt.json.example config/mqtt.json
```

4. Edit the configuration file config/mqtt.json and replace the entries in `chat_servers` with the `mqtt-websocket` address from the Preparation section above. For example, for a source-code deployment of `xiaozhi-server`, the configuration is:

``` 
{
    "production": {
        "chat_servers": [
            "ws://127.0.0.1:8000/xiaozhi/v1/?from=mqtt_gateway"
        ]
    },
    "debug": false,
    "max_mqtt_payload_size": 8192,
    "mcp_client": {
        "capabilities": {
        },
        "client_info": {
            "name": "xiaozhi-mqtt-client",
            "version": "1.0.0"
        },
        "max_tools_count": 128
    }
}
```
5. Create a `.env` file in the project root directory and set the following environment variables:
```
PUBLIC_IP=your-ip         # Server public IP
MQTT_PORT=1883            # MQTT server port
UDP_PORT=8884             # UDP server port
API_PORT=8007             # Management API port
MQTT_SIGNATURE_KEY=test   # MQTT signature key
SERVER_SECRET=Te1st12134  # Server secret; keep it consistent with the Control Panel (server.secret) or xiaozhi-server (server.auth_key)
```
Pay attention to the `PUBLIC_IP` setting: make sure it matches the actual public IP. If you have a domain name, enter the domain name.

`MQTT_SIGNATURE_KEY` is the key used for MQTT connection authentication. Set it to something complex, preferably at least 8 characters with both uppercase and lowercase letters. You will need this key later.

- Do not use simple passwords such as `123456` or `test`.
- Do not use simple passwords such as `123456` or `test`.
- Do not use simple passwords such as `123456` or `test`.

`SERVER_SECRET` is used to generate the authentication information for the WebSocket connection.

1. If you use a full-module deployment and `server.auth.enabled` is set to `true` in the Control Panel parameter management, `SERVER_SECRET` must match the Control Panel `server.secret`.

2. If you use a server-only deployment and `server.auth.enabled` is set to `true` in the configuration file, `SERVER_SECRET` must match `server.auth_key` in the configuration file.


6. Start the MQTT gateway:
```
# Start the service
pm2 start ecosystem.config.js

# View the logs
pm2 logs xz-mqtt
```

When you see logs like the following, the MQTT gateway has started successfully:
```
0|xz-mqtt  | 2025-09-11T12:14:48: MQTT server is listening on port 1883
0|xz-mqtt  | 2025-09-11T12:14:48: UDP server is listening on x.x.x.x:8884
```

To restart the MQTT gateway, run:
```
pm2 restart xz-mqtt
```

## Part 2: Full-Module Deployment with MQTT+UDP Connections for XiaoZhi Hardware

Check the version number at the bottom of the Control Panel home page and confirm that it is `0.7.7` or later. If not, upgrade the Control Panel.

1. At the top of the Control Panel, click `Parameter Management`, search for `server.mqtt_gateway`, click Edit, and enter the `PUBLIC_IP` + `:` + `MQTT_PORT` you set in the `.env` file. For example:
```
192.168.0.7:1883
```
2. At the top of the Control Panel, click `Parameter Management`, search for `server.mqtt_signature_key`, click Edit, and enter the `MQTT_SIGNATURE_KEY` you set in the `.env` file.

3. At the top of the Control Panel, click `Parameter Management`, search for `server.udp_gateway`, click Edit, and enter the `PUBLIC_IP` + `:` + `UDP_PORT` you set in the `.env` file. For example:
```
192.168.0.7:8884
```
4. At the top of the Control Panel, click `Parameter Management`, search for `server.mqtt_manager_api`, click Edit, and enter the `PUBLIC_IP` + `:` + `API_PORT` you set in the `.env` file. For example:
```
192.168.0.7:8007
```

After completing the configuration above, use a curl command to verify that your OTA address delivers the MQTT configuration. Replace `http://localhost:8002/xiaozhi/ota/` below with your own OTA address:
```
curl 'http://localhost:8002/xiaozhi/ota/' \
  -H 'Content-Type: application/json' \
  -H 'Client-Id: 7b94d69a-9808-4c59-9c9b-704333b38aff' \
  -H 'Device-Id: 11:22:33:44:55:66' \
  --data-raw $'{\n  "application": {\n    "version": "1.0.1",\n    "elf_sha256": "1"\n  },\n  "board": {\n    "mac": "11:22:33:44:55:66"\n  }\n}'
```

If the returned content includes `mqtt`-related configuration, the setup succeeded. For example:

```
{"server_time":{"timestamp":1757567894012,"timeZone":"Asia/Shanghai","timezone_offset":480},"activation":{"code":"460609","message":"http://xiaozhi.server.com\n460609","challenge":"11:22:33:44:55:66"},"firmware":{"version":"1.0.1","url":"http://xiaozhi.server.com:8002/xiaozhi/otaMag/download/NOT_ACTIVATED_FIRMWARE_THIS_IS_A_INVALID_URL"},"websocket":{"url":"ws://192.168.4.23:8000/xiaozhi/v1/"},"mqtt":{"endpoint":"192.168.0.7:1883","client_id":"GID_default@@@11_22_33_44_55_66@@@7b94d69a-9808-4c59-9c9b-704333b38aff","username":"eyJpcCI6IjA6MDowOjA6MDowOjA6MSJ9","password":"Y8XP9xcUhVIN9OmbCHT9ETBiYNE3l3Z07Wk46wV9PE8=","publish_topic":"device-server","subscribe_topic":"devices/p2p/11_22_33_44_55_66"}}
```

MQTT information is delivered through the OTA address, so as long as the device can connect to the server's OTA address normally, restart the device to wake it.

After waking it, check the mqtt-gateway logs to confirm whether a connection was established successfully.
```
pm2 logs xz-mqtt
```

## Part 3: Running xiaozhi-server as a Single Module with MQTT+UDP Connections for XiaoZhi Hardware

Open your `data/.config.yaml` file. Under `server`, find `mqtt_gateway` and enter the `PUBLIC_IP` + `:` + `MQTT_PORT` you set in the `.env` file. For example:
```
192.168.0.7:1883
```
Under `server`, find `mqtt_signature_key` and enter the `MQTT_SIGNATURE_KEY` you set in the `.env` file.

Under `server`, find `udp_gateway` and enter the `PUBLIC_IP` + `:` + `UDP_PORT` you set in the `.env` file. For example:
```
192.168.0.7:8884
```

After completing the configuration above, use a curl command to verify that your OTA address delivers the MQTT configuration. Replace `http://localhost:8002/xiaozhi/ota/` below with your own OTA address:
```
curl 'http://localhost:8002/xiaozhi/ota/' \
  -H 'Device-Id: 11:22:33:44:55:66' \
  --data-raw $'{\n  "application": {\n    "version": "1.0.1",\n    "elf_sha256": "1"\n  },\n  "board": {\n    "mac": "11:22:33:44:55:66"\n  }\n}'
```

If the returned content includes `mqtt`-related configuration, the setup succeeded. For example:
```
{"server_time":{"timestamp":1758781561083,"timeZone":"GMT+08:00","timezone_offset":480},"activation":{"code":"527111","message":"http://xiaozhi.server.com\n527111","challenge":"11:22:33:44:55:66"},"firmware":{"version":"1.0.1","url":"http://xiaozhi.server.com:8002/xiaozhi/otaMag/download/NOT_ACTIVATED_FIRMWARE_THIS_IS_A_INVALID_URL"},"websocket":{"url":"ws://192.168.1.15:8000/xiaozhi/v1/"},"mqtt":{"endpoint":"192.168.1.15:1883","client_id":"GID_default@@@11_22_33_44_55_66@@@11_22_33_44_55_66","username":"eyJpcCI6IjE5Mi4xNjguMS4xNSJ9","password":"fjAYs49zTJecWqJ3jBt+kqxVn/x7vkXRAc85ak/va7Y=","publish_topic":"device-server","subscribe_topic":"devices/p2p/11_22_33_44_55_66"}}
```

MQTT information is delivered through the OTA address, so as long as the device can connect to the server's OTA address normally, restart the device to wake it.

After waking it, check the mqtt-gateway logs to confirm whether a connection was established successfully.
```
pm2 logs xz-mqtt
```
