# Context Provider Usage Tutorial

## Overview

A `context provider` adds a [data source] to the context of the XiaoZhi system prompt.

At the moment XiaoZhi is woken, the `context provider` fetches data from external systems and dynamically injects it into the LLM's system prompt.
This lets XiaoZhi perceive the state of something in the world when it wakes up.

It is fundamentally different from MCP and memory: a `context provider` forces XiaoZhi to perceive world data; `memory (Mem)` tells it what was discussed before; `MCP (function_call)` is invoked only when a capability or piece of knowledge is needed.

With this feature, at the instant XiaoZhi wakes up, it "perceives":
- Human health sensor states (body temperature, blood pressure, blood oxygen, etc.)
- Real-time data from business systems (server load, to-do items, stock information, etc.)
- Any textual information obtainable through an HTTP API

**Note**: this feature only lets XiaoZhi perceive the state of things when it wakes up. If you want XiaoZhi to obtain real-time state after waking, combine this feature with MCP tool calls.

## How It Works

1. **Configure sources**: the user configures one or more HTTP API addresses.
2. **Trigger requests**: when the system builds the prompt, if the template contains the `{{ dynamic_context }}` placeholder, it requests all configured APIs.
3. **Automatic injection**: the system formats the API responses as a Markdown list and replaces the `{{ dynamic_context }}` placeholder.

## API Specification

For XiaoZhi to parse the data correctly, your API must meet the following requirements:

- **Request method**: `GET`
- **Request headers**: the system automatically adds a `device-id` field to the request headers.
- **Response format**: must return JSON containing `code` and `data` fields.

### Response Examples

**Case 1: return key-value pairs**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "Living room temperature": "26°C",
    "Living room humidity": "45%",
    "Front door status": "Closed"
  }
}
```
*Injection result:*
```markdown
<context>
- **Living room temperature:** 26°C
- **Living room humidity:** 45%
- **Front door status:** Closed
</context>
```

**Case 2: return a list**
```json
{
  "code": 0,
  "data": [
    "You have 10 to-do items",
    "The car is currently traveling at 100 km/h"
  ]
}
```
*Injection result:*
```markdown
<context>
- You have 10 to-do items
- The car is currently traveling at 100 km/h
</context>
```

## Configuration Guide

### Option 1: Control Panel Configuration (Full-Module Deployment)

1. Log in to the Control Panel and open the **Role Configuration** page.
2. Find the **Context Providers** setting (click the "Edit Sources" button).
3. Click **Add** and enter your API address.
4. If the API requires authentication, add `Authorization` or another header under **Request Headers**.
5. Save the configuration.

### Option 2: Configuration File (Server-Only Deployment)

Edit the `xiaozhi-server/data/.config.yaml` file and add a `context_providers` section:

```yaml
# Context provider configuration
context_providers:
  - url: "http://api.example.com/data"
    headers:
      Authorization: "Bearer your-token"
  - url: "http://another-api.com/data"
```

## Enabling the Feature

By default, the system prompt template file (`data/.agent-base-prompt.txt`) already contains the `{{ dynamic_context }}` placeholder, so you do not need to add it manually.

**Example:**

```markdown
<context>
[Important! The following information is provided in real time; do not call tools to query it—use it directly:]
- **Device ID:** {{device_id}}
- **Current time:** {{current_time}}
...
{{ dynamic_context }}
</context>
```

**Note**: if you do not need this feature, you can choose **not to configure any context provider**, or **remove** the `{{ dynamic_context }}` placeholder from the prompt template file.

## Appendix: Mock Test Service Example

To make testing and development easier, we provide a simple Python mock server script. You can run it to simulate API endpoints locally.

**mock_api_server.py**

```python
import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

# Set the port number
PORT = 8081

class MockRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the path and parameters
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        response_data = {}
        status_code = 200

        print(f"Received request: {path}, parameters: {query}")

        # Case 1: mock health data (returns a dict)
        # Path style: /health
        # device_id comes from the header
        if path == "/health":
            device_id = self.headers.get("device-id", "unknown_device")
            print(f"device_id: {device_id}")
            response_data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "Test device ID": device_id,
                    "Heart rate": "80 bpm",
                    "Blood pressure": "120/80 mmHg",
                    "Status": "Good"
                }
            }

        # Case 2: mock news list (returns a list)
        # No parameters: /news/list
        elif path == "/news/list":
            response_data = {
                "code": 0,
                "msg": "success",
                "data": [
                    "Today's headlines: Python 3.14 released",
                    "Tech news: AI assistants are changing lives",
                    "Local news: heavy rain tomorrow, remember your umbrella"
                ]
            }

        # Case 3: mock weather briefing (returns a string)
        # No parameters: /weather/simple
        elif path == "/weather/simple":
            response_data = {
                "code": 0,
                "msg": "success",
                "data": "Sunny turning cloudy today, 20-25°C, excellent air quality, good for going out."
            }

        # Case 4: mock device details (query parameter style)
        # Path style: /device/info
        # device_id comes from the header
        elif path == "/device/info":
            device_id = self.headers.get("device-id", "unknown_device")
            response_data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "Query method": "Header parameter",
                    "Device ID": device_id,
                    "Battery": "85%",
                    "Firmware": "v2.0.1"
                }
            }
        
        # Case 5: 404 Not Found
        else:
            status_code = 404
            response_data = {"error": "Endpoint does not exist"}

        # Send the response
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

# Start the service
# Allow address reuse to avoid errors on rapid restarts
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), MockRequestHandler) as httpd:
    print(f"==================================================")
    print(f"Mock API Server started: http://localhost:{PORT}")
    print(f"Available endpoints:")
    print(f"1. [dict] http://localhost:{PORT}/health")
    print(f"2. [list] http://localhost:{PORT}/news/list")
    print(f"3. [text] http://localhost:{PORT}/weather/simple")
    print(f"4. [parameters] http://localhost:{PORT}/device/info")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nService stopped")
```
