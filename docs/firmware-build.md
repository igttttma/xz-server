# ESP32 Firmware Compilation

## Step 1 Prepare Your OTA Address

If you are using version 0.3.12 of this project, you will have an OTA address whether you use a server-only deployment or a full-module deployment.

Because OTA address configuration differs between server-only and full-module deployments, choose the appropriate method below:

### If You Use a Server-Only Deployment
Open your OTA address in a browser. For example, my OTA address is:
```
http://192.168.1.25:8003/xiaozhi/ota/
```
If it displays "OTA endpoint is running normally. The websocket address sent to devices is: ws://xxx:8000/xiaozhi/v1/",

you can start the `digital-human` module and open `index.html` to test whether it can connect to the websocket address shown on the OTA page.

If it cannot connect, modify the `server.websocket` address in the configuration file `.config.yaml`, restart, and test again until `index.html` can connect normally.

Once it works, continue to Step 2.

### If You Use a Full-Module Deployment
Open your OTA address in a browser. For example, my OTA address is:
```
http://192.168.1.25:8002/xiaozhi/ota/
```

If it displays "OTA endpoint is running normally. Number of websocket clusters: X", continue to Step 2.

If it displays "OTA endpoint is not running normally", you probably have not configured the `Websocket` address in the `Control Panel`. Then:

- 1. Log in to the Control Panel as the super administrator.

- 2. Click `Parameter Management` in the top menu.

- 3. Find the `server.websocket` entry in the list and enter your `Websocket` address. For example, mine is:

```
ws://192.168.1.25:8000/xiaozhi/v1/
```

After configuring it, refresh your OTA endpoint URL in the browser to see whether it works. If it still does not, confirm again that Websocket started normally and that the Websocket address is configured.

## Step 2 Configure the Environment
First, configure the project environment by following this tutorial: [Setting Up the ESP-IDF 5.3.2 Development Environment on Windows and Compiling XiaoZhi](https://icnynnzcwou8.feishu.cn/wiki/JEYDwTTALi5s2zkGlFGcDiRknXf)

## Step 3 Open the Configuration File
After setting up the build environment, download the source code of Brother Xia's xiaozhi-esp32 project.

Download [the xiaozhi-esp32 project source code](https://github.com/78/xiaozhi-esp32) here.

After downloading, open the `xiaozhi-esp32/main/Kconfig.projbuild` file.

## Step 4 Modify the OTA Address

Find the `default` value of `OTA_URL` and change `https://api.tenclass.net/xiaozhi/ota/`
   to your own address. For example, if my endpoint address is `http://192.168.1.25:8002/xiaozhi/ota/`, change it to that.

Before:
```
config OTA_URL
    string "Default OTA URL"
    default "https://api.tenclass.net/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```
After:
```
config OTA_URL
    string "Default OTA URL"
    default "http://192.168.1.25:8002/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```

## Step 4 Set the Build Parameters

Set the build parameters:

```
# Enter the xiaozhi-esp32 root directory from the terminal
cd xiaozhi-esp32
# For example, I use an esp32s3 board, so I set the build target to esp32s3; if your board is another model, replace it with the corresponding model
idf.py set-target esp32s3
# Open the menu configuration
idf.py menuconfig
```

After entering menuconfig, go to `Xiaozhi Assistant` and set `BOARD_TYPE` to your specific board model.
Save and exit, then return to the terminal.

## Step 5 Build the Firmware

```
idf.py build
```

## Step 6 Package the bin Firmware

```
cd scripts
python release.py
```

After the packaging command completes, the firmware file `merged-binary.bin` is generated in the `build` directory under the project root.
This `merged-binary.bin` is the firmware file to flash onto the hardware.

Note: if the second command reports a "zip"-related error, ignore it as long as the firmware file `merged-binary.bin` is generated in the `build` directory.
It has little impact, so continue.

## Step 7 Flash the Firmware
   Connect the ESP32 device to your computer and open the following URL in Chrome:

```
https://espressif.github.io/esp-launchpad/
```

Open this tutorial: [Flash Tool / Web-based Firmware Flashing (No IDF Development Environment)](https://ccnphfhqs21z.feishu.cn/wiki/Zpz4wXBtdimBrLk25WdcXzxcnNS).
Go to `Method 2: ESP-Launchpad browser-based web flashing`, start from `3. Flash firmware/download to the development board`, and follow the tutorial.

After flashing and connecting to the network successfully, wake XiaoZhi with the wake word and watch the console output on the server side.

## FAQ
Here are some common questions for reference:

[1. Why does XiaoZhi recognize a lot of Korean, Japanese, and English when I speak?](./FAQ.md)

[2. Why do I get "TTS task error: file does not exist"?](./FAQ.md)

[3. TTS often fails or times out](./FAQ.md)

[4. I can connect to the self-hosted server over Wi-Fi, but not in 4G mode](./FAQ.md)

[5. How can I improve XiaoZhi's response speed?](./FAQ.md)

[6. I speak slowly, but XiaoZhi keeps interrupting during pauses](./FAQ.md)

[7. I want to use XiaoZhi to control lights, air conditioners, remote power switches, and more](./FAQ.md)
