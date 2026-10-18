# Weather Plugin Usage Guide

## Overview

The `get_weather` plugin is one of the core features of the XiaoZhi ESP32 voice assistant. It supports querying weather information across the country by voice. The plugin is based on the QWeather API and provides real-time weather and 7-day forecasts.

## API Key Application Guide

### 1. Register a QWeather Account

1. Visit the [QWeather console](https://console.qweather.com/).
2. Register an account and complete email verification.
3. Log in to the console.

### 2. Create an Application and Obtain an API Key

1. After entering the console, click ["Project Management"](https://console.qweather.com/project?lang=zh) on the right → "Create Project".
2. Fill in the project information:
   - **Project name**: for example, "XiaoZhi Voice Assistant"
3. Click Save.
4. After the project is created, click "Create Credential" in the project.
5. Fill in the credential information:
    - **Credential name**: for example, "XiaoZhi Voice Assistant"
    - **Authentication method**: select "API Key"
6. Click Save.
7. Copy the `API Key` from the credential; this is the first key configuration value.

### 3. Obtain the API Host

1. In the console, click ["Settings"](https://console.qweather.com/setting?lang=zh) → "API Host".
2. Note the dedicated `API Host` address assigned to you; this is the second key configuration value.

The steps above produce two important configuration values: `API Key` and `API Host`.

## Configuration Methods (Choose One)

### Option 1. If You Use a Control Panel Deployment (Recommended)

1. Log in to the Control Panel.
2. Open the "Role Configuration" page.
3. Select the agent to configure.
4. Click the "Edit Features" button.
5. Find the "Weather Query" plugin in the parameter configuration area on the right.
6. Check "Weather Query".
7. Enter the first key configuration value, `API Key`, in `Weather Plugin API Key`.
8. Enter the second key configuration value, `API Host`, in `Developer API Host`.
9. Save the configuration, then save the agent configuration.

### Option 2. If You Use Only a Server-Only xiaozhi-server Deployment

Configure it in `data/.config.yaml`:

1. Enter the first key configuration value, `API Key`, in `api_key`.
2. Enter the second key configuration value, `API Host`, in `api_host`.
3. Enter your city in `default_location`, for example `Guangzhou`.

```yaml
plugins:
  get_weather:
    api_key: "your QWeather API key"
    api_host: "your QWeather API host"
    default_location: "your default query city"
```

