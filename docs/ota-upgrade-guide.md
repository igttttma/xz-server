# Firmware OTA Automatic Upgrade Configuration Guide for Server-Only Deployment

This tutorial explains how to configure automatic firmware OTA upgrades in a **server-only deployment** so that device firmware updates automatically.

If you are using a **full-module deployment**, ignore this tutorial.

## Feature Overview

In a server-only deployment, xiaozhi-server includes built-in OTA firmware management. It automatically detects the device version and delivers upgrade firmware. The system matches and pushes the latest firmware version based on the device model and current version.

## Prerequisites

- You have successfully completed a **server-only deployment** and are running xiaozhi-server.
- The device can connect to the server normally.

## Step 1 Prepare the Firmware Files

### 1. Create the Firmware Directory

Firmware files must be placed in the `data/bin/` directory. If the directory does not exist, create it manually:

```bash
mkdir -p data/bin
```

### 2. Firmware File Naming Rules

Firmware files must follow this naming format:

```
{device-model}_{version}.bin
```

**Naming rules:**
- `device-model`: the device model name, such as `lichuang-dev` or `bread-compact-wifi`
- `version`: the firmware version, which must start with a digit and may contain digits, letters, dots, underscores, and hyphens, such as `1.6.6` or `2.0.0`
- The file extension must be `.bin`

**Naming examples:**
```
bread-compact-wifi_1.6.6.bin
lichuang-dev_2.0.0.bin
```

### 3. Place the Firmware Files

Copy the prepared firmware file (the .bin file) into the `data/bin/` directory:

Important, repeated three times: the bin file for upgrades is `xiaozhi.bin`, not the full firmware file `merged-binary.bin`!

Important, repeated three times: the bin file for upgrades is `xiaozhi.bin`, not the full firmware file `merged-binary.bin`!

Important, repeated three times: the bin file for upgrades is `xiaozhi.bin`, not the full firmware file `merged-binary.bin`!

```bash
cp xiaozhi.bin data/bin/device-model_version.bin
```

For example:
```bash
cp xiaozhi.bin data/bin/bread-compact-wifi_1.6.6.bin
```

## Step 2 Configure the Public Access Address (Public Deployment Only)

**Note: this step applies only to server-only deployments on the public internet.**

If your xiaozhi-server is deployed on the public internet (using a public IP or domain), you **must** configure the `server.vision_explain` parameter, because the OTA firmware download address uses the domain and port from that setting.

If you deploy on a LAN, you can skip this step.

### Why Configure This Parameter?

In a server-only deployment, the system uses the domain and port from `vision_explain` as the base address when generating firmware download URLs. If it is not configured or is configured incorrectly, devices cannot access the firmware download address.

### Configuration Method

Open the `data/.config.yaml` file, find the `server` section, and set the `vision_explain` parameter:

```yaml
server:
  vision_explain: http://your-domain-or-IP:port/mcp/vision/explain
```

**Configuration examples:**

LAN deployment (default):
```yaml
server:
  vision_explain: http://192.168.1.100:8003/mcp/vision/explain
```

Public domain deployment:
```yaml
server:
  vision_explain: http://yourdomain.com:8003/mcp/vision/explain
```

### Notes

- The domain or IP must be reachable by the device.
- If you deploy with Docker, do not use internal Docker addresses (such as 127.0.0.1 or localhost).
- If you use an Nginx reverse proxy, enter the external address and port, not the port this project listens on.


## FAQ

### 1. The device does not receive firmware updates

**Possible causes and solutions:**

- Check whether the firmware file name follows the rule: `{model}_{version}.bin`
- Check whether the firmware file is placed correctly in the `data/bin/` directory
- Check whether the device model matches the model in the firmware file name
- Check whether the firmware version is newer than the device's current version
- Check the server logs to confirm that OTA requests are handled correctly

### 2. The device reports that the download address is unreachable

**Possible causes and solutions:**

- Check whether the domain or IP configured in `server.vision_explain` is correct
- Confirm that the port is correct (default 8003)
- For a public deployment, make sure the device can reach that public address
- For a Docker deployment, make sure you are not using an internal address (127.0.0.1)
- Check whether the firewall allows the corresponding port
- If you use an Nginx reverse proxy, enter the external address and port, not the port this project listens on

### 3. How to confirm the device's current version

Check the OTA request logs; the version reported by the device appears in the logs:

```
[ota_handler] - Device AA:BB:CC:DD:EE:FF firmware is already up to date: 1.6.6
```

### 4. The firmware file does not take effect after being placed

The system caches for 30 seconds by default. You can:
- Wait 30 seconds before having the device send another OTA request
- Restart the xiaozhi-server service
- Set `firmware_cache_ttl` to a shorter duration
