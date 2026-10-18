# get_news_from_newsnow Plugin News Source Configuration Guide

## Overview

The `get_news_from_newsnow` plugin now supports dynamic news source configuration through the web management interface, so you no longer need to modify code. Users can configure different news sources for each agent in the Control Panel.

## Configuration Methods

### 1. Configure Through the Web Management Interface (Recommended)

1. Log in to the Control Panel.
2. Open the "Role Configuration" page.
3. Select the agent to configure.
4. Click the "Edit Features" button.
5. Find the "newsnow news aggregation" plugin in the parameter configuration area on the right.
6. Enter semicolon-separated names in the "News Source Configuration" field.

### 2. Configuration File Method

Configure it in `config.yaml`:

```yaml
plugins:
  get_news_from_newsnow:
    url: "https://newsnow.busiyi.world/api/s?id="
    news_sources: "The Paper;Baidu Hot Search;CLS;Weibo;Douyin"
```

## News Source Configuration Format

The news source configuration uses semicolon-separated names in this format:

```
name1;name2;name3
```

### Configuration Example

```
The Paper;Baidu Hot Search;CLS;Weibo;Douyin;Zhihu;36Kr
```

## Supported News Sources

The plugin supports the following news sources by name:

- The Paper
- Baidu Hot Search
- CLS
- Weibo
- Douyin
- Zhihu
- 36Kr
- Wallstreetcn
- ITHome
- Toutiao
- Hupu
- Bilibili
- Kuaishou
- Xueqiu
- Gelonghui
- FastBull
- Jin10
- Nowcoder
- SSPAI
- Juejin
- ifeng
- Chongbuluo
- Lianhe Zaobao
- Coolapk
- PCbeta
- Cankaoxiaoxi
- Sputnik
- Baidu Tieba
- Kaopu News
- And more...

## Default Configuration

If no news sources are configured, the plugin uses the following defaults:

```
The Paper;Baidu Hot Search;CLS
```

## Usage

1. **Configure news sources**: set the news source names in the web interface or configuration file, separated by semicolons.
2. **Invoke the plugin**: the user can say "read the news" or "get the news".
3. **Specify a news source**: the user can say "read The Paper" or "get Baidu Hot Search".
4. **Get details**: the user can say "tell me more about this news item".

## How It Works

1. The plugin accepts a name as a parameter (such as "The Paper").
2. Based on the configured news source list, it maps the name to the corresponding English ID (such as "thepaper").
3. It calls the API with the English ID to fetch news data.
4. It returns the news content to the user.

## Notes

1. Configured names must exactly match those defined in CHANNEL_MAP.
2. After changing the configuration, restart the service or reload the configuration.
3. If a configured news source is invalid, the plugin automatically falls back to the default news sources.
4. Separate multiple news sources with an English semicolon (;), not a full-width semicolon (；).
