# PowerMem Memory Component Integration Guide

## Introduction

[PowerMem](https://www.powermem.ai/) is an agent memory component open-sourced by OceanBase. It summarizes memories and performs intelligent retrieval with a local LLM, providing efficient memory management for AI agents.

Cost notes: PowerMem itself is open source and free. Actual costs depend on the LLM and database you choose:
- Using SQLite + a free LLM (such as Zhipu glm-4-flash) = **completely free**
- Using a cloud LLM or cloud database = billed by the corresponding service

> 💡 **Best performance tip**: PowerMem delivers maximum performance when used with OceanBase. Use SQLite only when resources are limited.

- **GitHub**: https://github.com/oceanbase/powermem
- **Website**: https://www.powermem.ai/
- **Examples**: https://github.com/oceanbase/powermem/tree/main/examples

## Features

- **Local summarization**: memory summarization and extraction are performed locally through an LLM
- **User profile**: `UserMemory` automatically extracts user information (name, occupation, interests, etc.) and continuously updates the user profile
- **Intelligent forgetting**: automatically "forgets" outdated noise based on the Ebbinghaus forgetting curve
- **Multiple storage backends**: supports OceanBase (recommended, best performance), SeekDB (recommended, all-in-one AI application storage), PostgreSQL, and SQLite (lightweight alternative)
- **Multiple LLMs**: Qwen, Zhipu (glm-4-flash is free), OpenAI, etc.
- **Intelligent retrieval**: semantic retrieval based on vector search
- **Private deployment**: fully supports local private deployment
- **Asynchronous operations**: efficient asynchronous memory management

## Installation

PowerMem is already included in the project dependencies. To install it manually:

```bash
pip install powermem
```

## Configuration

### Basic Configuration

Configure PowerMem in `config.yaml`:

```yaml
selected_module:
  Memory: powermem

Memory:
  powermem:
    type: powermem
    # Whether to enable the user profile feature
    # User profile supports: oceanbase, seekdb, sqlite (powermem 0.3.0+)
    enable_user_profile: true
    
    # ========== LLM configuration ==========
    llm:
      provider: openai  # Optional: qwen, openai, zhipu, etc.
      config:
        api_key: your LLM API key
        model: qwen-plus
        # openai_base_url: https://api.openai.com/v1  # Optional, custom service URL
    
    # ========== Embedding configuration ==========
    embedder:
      provider: openai  # Optional: qwen, openai, etc.
      config:
        api_key: your embedding model API key
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
        # embedding_dims: 1024  # Vector dimensions; required when not 1536
    
    # ========== Database configuration ==========
    vector_store:
      provider: sqlite  # Optional: oceanbase (recommended), seekdb (recommended), postgres, sqlite (lightweight)
      config: {}  # SQLite requires no extra configuration
```

### Configuration Parameters

#### LLM Configuration

| Parameter | Description | Possible Values |
|------|------|--------|
| `llm.provider` | LLM provider | `qwen`, `openai`, `zhipu`, etc. |
| `llm.config.api_key` | API key | - |
| `llm.config.model` | Model name | Depends on the provider |
| `llm.config.openai_base_url` | Custom service URL (optional) | - |

#### Embedding Configuration

| Parameter | Description | Possible Values |
|------|------|--------|
| `embedder.provider` | Embedding model provider | `qwen`, `openai`, etc. |
| `embedder.config.api_key` | API key | - |
| `embedder.config.model` | Model name | Depends on the provider |
| `embedder.config.openai_base_url` | Custom service URL (optional) | - |

#### Database Configuration

| Parameter | Description | Possible Values |
|------|------|--------|
| `vector_store.provider` | Storage backend type | `oceanbase` (recommended), `seekdb` (recommended), `postgres`, `sqlite` (lightweight) |
| `vector_store.config` | Database connection configuration | Set according to the provider |

### Memory Modes

PowerMem supports two memory modes:

| Mode | Configuration | Features | Storage Requirements |
|------|------|------|----------|
| **Standard memory** | `enable_user_profile: false` | Conversation memory storage and retrieval | Supports all databases |
| **User profile** | `enable_user_profile: true` | Memory + automatic user profile extraction | oceanbase, seekdb, sqlite |

> 📌 **Version note**: PowerMem 0.3.0+ supports OceanBase, SeekDB, and SQLite as storage backends for the user profile feature.

### Using Qwen (Recommended)

1. Visit the [Alibaba Cloud Bailian platform](https://bailian.console.aliyun.com/) and register an account.
2. Obtain an API key from the [API Key management](https://bailian.console.aliyun.com/?apiKey=1#/api-key) page.
3. Configure as follows:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: qwen
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: sqlite
      config: {}
```

### Using Zhipu's Free LLM (Completely Free Setup)

Zhipu provides the free glm-4-flash model, which combined with SQLite enables completely free usage:

1. Visit the [Zhipu AI open platform](https://bigmodel.cn/) and register an account.
2. Obtain an API key from the [API Keys](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) page.
3. Configure as follows:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: openai  # Use OpenAI-compatible mode
      config:
        api_key: xxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
        model: glm-4-flash
        openai_base_url: https://open.bigmodel.cn/api/paas/v4/
    embedder:
      provider: openai
      config:
        api_key: xxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
        model: embedding-3
        openai_base_url: https://open.bigmodel.cn/api/paas/v4/
    vector_store:
      provider: sqlite
      config: {}
```

### Using OpenAI

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: gpt-4o-mini
        openai_base_url: https://api.openai.com/v1
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-3-small
        openai_base_url: https://api.openai.com/v1
    vector_store:
      provider: sqlite
      config: {}
```

### Using OceanBase (Best Performance)

OceanBase is PowerMem's ideal partner and unlocks maximum performance:

1. Deploy an OceanBase database (open-source local deployment or a cloud service).
   - Open-source deployment: https://github.com/oceanbase/oceanbase
   - Cloud service: https://www.oceanbase.com/
2. Configure as follows:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: qwen
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: oceanbase
      config:
        host: 127.0.0.1
        port: 2881
        user: root@test
        password: your_password
        db_name: powermem
        collection_name: memories  # Default value
        embedding_model_dims: 1536  # Embedding vector dimensions; required
```

## Device Memory Isolation

PowerMem automatically uses the device ID (`device_id`) as `user_id` for memory isolation. This means:

- Each device has its own independent memory space
- Memories are completely isolated between different devices
- Multiple conversations on the same device share the memory context

## User Profile (UserMemory)

PowerMem provides a `UserMemory` class that can automatically extract user profile information from conversations.

> 📌 **Version note**: PowerMem 0.3.0+ supports OceanBase, SeekDB, and SQLite as storage backends for the user profile feature.

### Enabling the User Profile

Set `enable_user_profile: true` in the configuration to enable it:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true  # Enable the user profile
    llm:
      provider: qwen
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: sqlite  # User profile supports: oceanbase, seekdb, sqlite
      config: {}
```

### User Profile Capabilities

| Capability | Description |
|------|------|
| **Information extraction** | Automatically extracts names, ages, occupations, interests, etc. from conversations |
| **Continuous updates** | Continuously refines the user profile as conversations progress |
| **Profile retrieval** | Combines user profiles with memory search to improve retrieval relevance |
| **Intelligent forgetting** | Fades outdated information based on the Ebbinghaus forgetting curve |

### How It Works

When the user profile is enabled, XiaoZhi automatically returns the following when querying memory:
1. **User profile**: the user's basic information, interests, and hobbies
2. **Related memories**: historical memories relevant to the current conversation

> ✅ **Version note**: PowerMem 0.3.0+ supports OceanBase, SeekDB, and SQLite as storage backends for the user profile feature.

## Comparison with Other Memory Components

| Feature | PowerMem | mem0ai | mem_local_short |
|------|----------|--------|-----------------|
| Working mode | Local summarization | Cloud API | Local summarization |
| Storage location | Local/cloud DB | Cloud | Local YAML |
| Cost | Depends on LLM and DB | 1,000 requests/month free | Completely free |
| Intelligent retrieval | ✅ Vector search | ✅ Vector search | ❌ Full return |
| User profile | ✅ UserMemory | ❌ | ❌ |
| Intelligent forgetting | ✅ Forgetting curve | ❌ | ❌ |
| Private deployment | ✅ Supported | ❌ Cloud only | ✅ Supported |
| Database support | OceanBase (recommended)/SeekDB/PostgreSQL/SQLite | - | YAML file |

## FAQ

### 1. Invalid API key

If you get an `API key is required` error, check:
- Whether `llm_api_key` and `embedding_api_key` are filled in correctly
- Whether the API key is valid

### 2. Model does not exist

If you get a model-not-found error, check:
- Whether the `llm_model` and `embedding_model` names are correct
- Whether the corresponding model service has been activated

### 3. Connection timeout

If you get a connection timeout, try:
- Checking the network connection
- Configuring `llm_base_url` and `embedding_base_url` if you use a proxy

## Verification

You can test whether PowerMem works in a virtual environment:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Test the PowerMem import
python -c "from powermem import AsyncMemory; print('PowerMem imported successfully')"

# Test the UserMemory import (user profile feature)
python -c "from powermem import UserMemory; print('UserMemory imported successfully')"
```

## More Resources

- [PowerMem documentation](https://www.powermem.ai/)
- [PowerMem GitHub repository](https://github.com/oceanbase/powermem)
- [PowerMem examples](https://github.com/oceanbase/powermem/tree/main/examples)
- [OceanBase website](https://www.oceanbase.com/)
- [OceanBase GitHub](https://github.com/oceanbase/oceanbase)
- [SeekDB GitHub](https://github.com/oceanbase/seekdb) (AI-native search database)
- [Alibaba Cloud Bailian platform](https://bailian.console.aliyun.com/)

