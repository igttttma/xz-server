# Web Search Plugin Usage Guide

## Feature Overview

The `web_search` plugin supports real-time web searches during conversations and returns the results. It supports three search providers: Metaso, Tavily, and Serply; choose the one you need.

## API Key Application Guide

We currently support `Metaso Search`, `Tavily Search`, and `Serply Search`.
- Tavily Search: 1,000 free searches per month.
- Metaso Search: provides relatively high-quality Chinese data sources.
- Serply Search: returns Google search results; new registrations receive 2,500 free searches, after which payment is required.

## API Key Application Guide

### Option 1: Use Metaso Search

- Visit the [Metaso Search API](https://metaso.cn/search-api/api-keys) and register/log in.
- On the API key management page, click "Create new Key".
- Copy the generated API key (prefixed with `mk-`); this is the required configuration information.

### Option 2: Use Tavily Search

- Visit the [Tavily console](https://app.tavily.com/home) and register/log in.
- Create an API key in the console.
- Copy the generated API key (prefixed with `tvly-`); this is the required configuration information.

### Option 3: Use Serply Search

- Visit [Serply](https://serply.io) and register/log in.
- Create an API key in the console.
- Copy the generated API key; this is the required configuration information.
- See the [Serply documentation](https://serply.io/docs) for API details.

## Configuration Methods

### Option 1. Control Panel Deployment (Recommended)

- Log in to the Control Panel.
- Open the "Role Configuration" page and select the agent to configure.
- Click the "Edit Features" button and find the "Web Search" plugin in the parameter configuration area on the right.
- Check "Web Search".
- Enter the search provider (`metaso`, `tavily`, or `serply`) and the corresponding `API Key` in the configuration fields.
- Save the configuration, then save the agent configuration.

### Option 2. Server-Only xiaozhi-server Deployment

Configure it in `data/.config.yaml`:

- Set the search provider in `provider`; valid values are `metaso`, `tavily`, or `serply`.
- Set the API key you obtained in `api_key`.

```yaml
plugins:
  web_search:
    provider: "metaso"
    api_key: "your API key"
```

To customize the number of returned results and the tool description, you can also configure `max_results` and `description`:

```yaml
plugins:
  web_search:
    provider: "metaso"
    description: "Web search tool. Use this tool when the user explicitly needs a web search."
    max_results: 5
    api_key: "your API key"
```

Also make sure `web_search` is enabled in the `functions` list:

```yaml
plugins:
  functions:
    - web_search
```

Restart the service after configuration for the changes to take effect.
