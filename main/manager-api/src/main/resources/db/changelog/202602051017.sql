-- Add the powermem memory model provider
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`)
VALUES ('SYSTEM_Memory_powermem', 'Memory', 'powermem', 'PowerMem Memory', '[
  {"key":"enable_user_profile","label":"Enable User Profile","type":"boolean"},
  {"key":"llm_provider","label":"LLM Provider","type":"string"},
  {"key":"llm_api_key","label":"LLM API Key","type":"string"},
  {"key":"llm_model","label":"LLM Model","type":"string"},
  {"key":"openai_base_url","label":"OpenAI Base URL","type":"string"},
  {"key":"embedding_provider","label":"Embedding Provider","type":"string"},
  {"key":"embedding_api_key","label":"Embedding API Key","type":"string"},
  {"key":"embedding_model","label":"Embedding Model","type":"string"},
  {"key":"embedding_openai_base_url","label":"Embedding OpenAI Base URL","type":"string"},
  {"key":"embedding_dims","label":"Embedding Dimension","type":"integer"},
  {"key":"vector_store","label":"Vector Store Configuration (JSON)","type":"dict"}
]', 4, 1, NOW(), 1, NOW());

-- Add the PowerMem memory model configuration
INSERT INTO `ai_model_config` VALUES (
  'Memory_powermem',
  'Memory',
  'powermem',
  'PowerMem Memory',
  0,
  1,
  '{\"type\": \"powermem\", \"enable_user_profile\": true, \"llm_provider\": \"openai\", \"llm_api_key\": \"your LLM API key\", \"llm_model\": \"qwen-plus\", \"openai_base_url\": \"\", \"embedding_provider\": \"openai\", \"embedding_api_key\": \"your embedding model API key\", \"embedding_model\": \"text-embedding-v4\", \"embedding_openai_base_url\": \"https://api.openai.com/v1\", \"embedding_dims\": \"\", \"vector_store\": {\"provider\": \"sqlite\", \"config\": {}}}',
  NULL,
  NULL,
  4,
  NULL,
  NULL,
  NULL,
  NULL
);


-- PowerMem memory configuration
UPDATE `ai_model_config` SET
`doc_link` = 'https://github.com/oceanbase/powermem',
`remark` = 'PowerMem is an open-source agent memory component from OceanBase that summarizes memories through a local LLM
GitHub: https://github.com/oceanbase/powermem
Website: https://www.powermem.ai/
Examples: https://github.com/oceanbase/powermem/tree/main/examples

[Cost]
PowerMem itself is free; actual cost depends on the chosen LLM and database:
- sqlite + a free LLM (such as glm-4-flash) = completely free
- a cloud LLM or cloud database = billed according to the corresponding service

[enable_user_profile] User profile feature
- false: use the normal memory mode (AsyncMemory)
- true: use the user profile mode (UserMemory) to automatically extract user information
- The user profile feature supports: oceanbase, seekdb, sqlite (powermem 0.3.0+)

[llm] LLM configuration - used for memory summarization and user profile extraction
  provider: LLM provider, options:
    - qwen: Qwen (https://bailian.console.aliyun.com/?apiKey=1#/api-key)
    - openai: OpenAI-compatible API
    - zhipu: Zhipu AI (https://bigmodel.cn/usercenter/proj-mgmt/apikeys) - the free glm-4-flash is recommended
  config: LLM configuration parameters
    - api_key: API key (required)
    - model: model name, such as qwen-plus or glm-4-flash
    - openai_base_url: custom service URL (optional), such as https://api.openai.com/v1
  Examples:
    {"provider": "zhipu", "config": {"api_key": "your_key", "model": "glm-4-flash"}}
    {"provider": "qwen", "config": {"api_key": "your_key", "model": "qwen-plus"}}

[embedder] Embedding configuration - used to vectorize memory content
  provider: embedding model provider, options:
    - qwen: Qwen
    - openai: OpenAI-compatible API
  config: Embedding configuration parameters
    - api_key: API key (required)
    - model: model name, such as text-embedding-v4 or text-embedding-3-small
    - openai_base_url: custom service URL (optional)
    - embedding_dims: vector dimension (optional); required when it is not 1536
  Example:
    {"provider": "openai", "config": {"api_key": "your_key", "model": "text-embedding-v4", "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}}

[vector_store] Database storage configuration - used to store vectorized memories
  provider: database type, options:
    - sqlite: lightweight local database (recommended for getting started, no extra configuration)
    - oceanbase: OceanBase database (recommended for production, best performance)
    - seekdb: SeekDB (recommended, all-in-one storage for AI applications)
    - postgres: PostgreSQL database

  SQLite configuration (no extra configuration needed):
    {"provider": "sqlite", "config": {}}

  OceanBase configuration example:
    {"provider": "oceanbase", "config": {
      "host": "127.0.0.1",
      "port": 2881,
      "user": "root@test",
      "password": "your_password",
      "db_name": "powermem",
      "collection_name": "memories",
      "embedding_model_dims": 1024
    }}
  Notes:
    - collection_name: default table name; if created with the wrong dimension, delete this table or change the name
    - embedding_model_dims: embedding vector dimension, which must match the model dimension of the embedder
      For example, for Zhipu: embedding-2 has dimension 1024, embedding-3 has dimension 2048

[Recommended configuration combinations]
1. Completely free setup:
   - LLM: zhipu + glm-4-flash (free)
   - Embedder: Qwen text-embedding-v4
   - Database: sqlite

2. Production setup:
   - LLM: qwen-plus or another commercial model
   - Embedder: text-embedding-v4
   - Database: oceanbase or seekdb
'
WHERE `id` = 'Memory_powermem';
