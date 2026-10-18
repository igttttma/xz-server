# How to Obtain Device Information with MCP Methods

This tutorial explains how to obtain device information with MCP methods.

Step 1: Customize your `agent-base-prompt.txt` file.

Copy the contents of the `agent-base-prompt.txt` file from the xiaozhi-server directory into your `data` directory and rename it to `.agent-base-prompt.txt`.

Step 2: Modify the `data/.agent-base-prompt.txt` file, find the `<context>` tag, and add the following code inside the tag:
```
- **Device ID:** {{device_id}}
```

After adding it, the `<context>` tag in your `data/.agent-base-prompt.txt` file should look roughly like this:
```
<context>
[Important! The following information is provided in real time; do not call tools to query it—use it directly:]
- **Device ID:** {{device_id}}
- **Current time:** {{current_time}}
- **Today's date:** {{today_date}} ({{today_weekday}})
- **Today's lunar date:** {{lunar_date}}
- **User's city:** {{local_address}}
- **Local weather for the next 7 days:** {{weather_info}}
</context>
```

Step 3: Modify the `data/.config.yaml` file, find the `agent-base-prompt` setting. Before modification it is:
```
prompt_template: agent-base-prompt.txt
```
Change it to:
```
prompt_template: data/.agent-base-prompt.txt
```

Step 4: Restart your xiaozhi-server service.

Step 5: Add a parameter named `device_id`, of type `string`, with the description `Device ID`, to your MCP method.

Step 6: Wake XiaoZhi again, have it call the MCP method, and check whether your MCP method can obtain the `Device ID`.
