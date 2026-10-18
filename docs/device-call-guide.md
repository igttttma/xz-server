# Device-to-Device Calling Plugin Usage Guide

## Overview

The device calling feature lets two configured devices communicate bidirectionally over voice/data channels. When device A calls device B, the system follows this flow:

```
Device A → authorization check → MQTT gateway → remote wake-up of device B → connection established → call established
```
## Prerequisites for Using This Feature
1. You must have at least two devices, and each device model must be `ESP32-S3`, because only `ESP32-S3` supports remote wake-up.
2. Your device must have `two microphones`. However, if your device has only a `single microphone` and you just want to try the feature, that works too, but you will experience severe stuttering.
3. You must deploy this project using the [full-module deployment](Deployment_all.md), because you need the `Control Panel` to manage device permissions and communication.
4. You must install and configure the [MQTT gateway service](mqtt-gateway-integration.md) from `May 27, 2026` or later. If you have already deployed the MQTT gateway service, confirm that the code version is from `May 27, 2026` or later.

These are the hard requirements for using this feature; details follow.

## Configuration Steps

### Step 1: Enable the Contacts Feature

1. Confirm that your Control Panel version is `0.9.4` or later.
2. Log in to the Control Panel.
3. Go to **System Feature Configuration**.
4. In the feature list on the left, check **Contacts**.
5. Click **Save Configuration** to confirm.

### Step 2: Configure Device-to-Device Calling Permissions

1. Click **Contacts** in the top menu of the Control Panel.
2. In the device list under the agent on the left, select your device A (search by MAC address or note name).
3. In the details panel on the right, find the label setting for target device B, for example **"Xiao Wang"**.
4. Check device B's **Calling Permission** checkbox.
5. Click **Save**.

**Bidirectional authorization:** For devices A and B to communicate with each other, you must configure the other side's permission separately in each device's Control Panel entry. For example:

- Check device B in device A's configuration → device A can communicate with device B
- Check device A in device B's configuration → device B can communicate with device A

### Step 3: Add the Calling Tool to the Agent Configuration

1. Click **Agent Management** in the top menu of the Control Panel.
2. In the agent that contains the device contacts you just configured, click **Edit Role**.
3. In the details panel on the right, click **Edit Features**.
4. Check the **Device Calls Device** tool.
5. Click **Save Configuration** to confirm.
6. Click **Save Configuration** again on the outer page, then restart the device.

### Step 4: Add the Remote Wake-Up Tool to the Firmware

1. Based on the [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) code, add a remote wake-up MCP tool. Supported versions are 2.1.0 to 2.2.6 (the version from May 29, 2026).
2. Add the remote wake-up function declaration in the application.h file:
    ```cpp
    void RemoteWakeup(const std::string& reason);
    ```
3. Add the remote wake-up function in the application.cc file:
    ```cpp
    void Application::RemoteWakeup(const std::string& reason){
        if (!protocol_) {
            return;
        }

        auto state = GetDeviceState();
        
        if (state == kDeviceStateIdle) {
            audio_service_.EncodeWakeWord();

            if (!protocol_->IsAudioChannelOpened()) {
                SetDeviceState(kDeviceStateConnecting);
                if (!protocol_->OpenAudioChannel()) {
                    audio_service_.EnableWakeWordDetection(true);
                    return;
                }
            }
            std::string wake_word = reason;
    #if CONFIG_USE_AFE_WAKE_WORD || CONFIG_USE_CUSTOM_WAKE_WORD
            // Encode and send the wake word data to the server
            while (auto packet = audio_service_.PopWakeWordPacket()) {
                protocol_->SendAudio(std::move(packet));
            }
            // Set the chat state to wake word detected
            protocol_->SendWakeWordDetected(wake_word);
            SetListeningMode(aec_mode_ == kAecOff ? kListeningModeAutoStop : kListeningModeRealtime);
    #else
            // Set flag to play popup sound after state changes to listening
            // (PlaySound here would be cleared by ResetDecoder in EnableVoiceProcessing)
            play_popup_on_listening_ = true;
            SetListeningMode(aec_mode_ == kAecOff ? kListeningModeAutoStop : kListeningModeRealtime);
    #endif
        } else if (state == kDeviceStateSpeaking) {
            AbortSpeaking(kAbortReasonWakeWordDetected);
            SetDeviceState(kDeviceStateIdle);
        } else if (state == kDeviceStateActivating) {
            SetDeviceState(kDeviceStateIdle);
        }
    }
    ```
4. Add the remote wake-up tool in the mcp_server.cc file:
    ```cpp
    AddUserOnlyTool("self.remote_wakeup", "Remote wakeup function with configurable parameters",
        PropertyList({
            Property("reason", kPropertyTypeString, "Wakeup reason"),
        }),
        [this](const PropertyList& properties) -> ReturnValue {
            std::string reason = properties["reason"].value<std::string>();
            ESP_LOGI(TAG, "Wakeup reason=%s", reason.c_str());
            auto& app = Application::GetInstance();
            app.RemoteWakeup(reason);
            return true;
    ```
5. Complete the firmware flash according to the [Firmware Compilation and Flashing Guide](firmware-build.md).
6. Whether your device has a single or dual microphone, be sure to enable AEC during compilation!
7. Whether your device has a single or dual microphone, be sure to enable AEC during compilation!
8. Whether your device has a single or dual microphone, be sure to enable AEC during compilation!

### Step 5: Configure the MQTT Gateway Service

1. Deploy the MQTT gateway service; see the [MQTT Gateway Integration Guide](mqtt-gateway-integration.md).
2. If it is already deployed, confirm that the code version is from May 27, 2026.

## Calling Flow

Prepare two devices. After configuring communication permissions in the Control Panel and adding the calling tool to the agent, say "Call XXX" to one of the XiaoZhi devices and observe whether device B responds.

## FAQ

### Q: Device B does not respond to the call?

- Check whether device B is online (device status in the Control Panel).
- Confirm that device B's firmware has correctly integrated the remote wake-up tool.
- Check whether the MQTT gateway connection is working.
- Verify that the bidirectional permission configuration is complete.

### Q: It says "No calling permission"?

- In the Control Panel, confirm that device A has device B's calling permission checked.
- Confirm that the configuration was saved (not merely modified but unsaved).

### Q: How can I confirm that the Contacts feature is enabled?

- If the Control Panel's top menu shows a "Contacts" entry, the feature is enabled.

### Q: I ask it to call "Zhang Shan", but it always recognizes "Zhang San". What can I do?
- Consult the documentation of the ASR service you use to confirm whether it supports hot word recognition.
- If you use `FunASRServer`, add "Zhang Shan" to the `hot word file` in the container, then restart the container.
- If you use `Volcano Engine` services, add a `hot word file` in the `Volcano Engine console`, then go back to the Control Panel's `Model Configuration page` and configure the `hot word file name` under `Volcano Engine TTS`.

