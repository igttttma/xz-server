-- Model provider table
DROP TABLE IF EXISTS `ai_model_provider`;
CREATE TABLE `ai_model_provider` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `model_type` VARCHAR(20) COMMENT 'Model type (Memory/ASR/VAD/LLM/TTS)',
    `provider_code` VARCHAR(50) COMMENT 'Provider type',
    `name` VARCHAR(50) COMMENT 'Provider name',
    `fields` JSON COMMENT 'Provider field list (JSON format)',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_provider_model_type` (`model_type`) COMMENT 'Index on the model type for quickly finding all providers of a given type'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Model configuration table';

-- Model configuration table
DROP TABLE IF EXISTS `ai_model_config`;
CREATE TABLE `ai_model_config` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `model_type` VARCHAR(20) COMMENT 'Model type (Memory/ASR/VAD/LLM/TTS)',
    `model_code` VARCHAR(50) COMMENT 'Model code (e.g. AliLLM, DoubaoTTS)',
    `model_name` VARCHAR(50) COMMENT 'Model name',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT 'Whether it is the default configuration (0: no, 1: yes)',
    `is_enabled` TINYINT(1) DEFAULT 0 COMMENT 'Whether enabled',
    `config_json` JSON COMMENT 'Model configuration (JSON format)',
    `doc_link` VARCHAR(200) COMMENT 'Official documentation link',
    `remark` VARCHAR(255) COMMENT 'Remark',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_config_model_type` (`model_type`) COMMENT 'Index on the model type for quickly finding all configurations of a given type'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Model configuration table';

-- TTS voice table
DROP TABLE IF EXISTS `ai_tts_voice`;
CREATE TABLE `ai_tts_voice` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `tts_model_id` VARCHAR(32) COMMENT 'Corresponding TTS model primary key',
    `name` VARCHAR(20) COMMENT 'Voice name',
    `tts_voice` VARCHAR(50) COMMENT 'Voice code',
    `languages` VARCHAR(50) COMMENT 'Language',
    `voice_demo` VARCHAR(500) DEFAULT NULL COMMENT 'Voice demo',
    `remark` VARCHAR(255) COMMENT 'Remark',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_tts_voice_tts_model_id` (`tts_model_id`) COMMENT 'Index on the TTS model primary key for quickly finding voice information of the corresponding model'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS voice table';

-- Agent configuration template table
DROP TABLE IF EXISTS `ai_agent_template`;
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent unique identifier',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(64) COMMENT 'Agent name',
    `asr_model_id` VARCHAR(32) COMMENT 'ASR model identifier',
    `vad_model_id` VARCHAR(64) COMMENT 'Voice activity detection identifier',
    `llm_model_id` VARCHAR(32) COMMENT 'LLM identifier',
    `tts_model_id` VARCHAR(32) COMMENT 'TTS model identifier',
    `tts_voice_id` VARCHAR(32) COMMENT 'Voice identifier',
    `mem_model_id` VARCHAR(32) COMMENT 'Memory model identifier',
    `intent_model_id` VARCHAR(32) COMMENT 'Intent model identifier',
    `system_prompt` TEXT COMMENT 'Role setting parameters',
    `lang_code` VARCHAR(10) COMMENT 'Language code',
    `language` VARCHAR(10) COMMENT 'Interaction language',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
    `creator` BIGINT COMMENT 'Creator ID',
    `created_at` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater ID',
    `updated_at` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent configuration template table';

-- Agent configuration table
DROP TABLE IF EXISTS `ai_agent`;
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent unique identifier',
    `user_id` BIGINT COMMENT 'Associated user ID',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(64) COMMENT 'Agent name',
    `asr_model_id` VARCHAR(32) COMMENT 'ASR model identifier',
    `vad_model_id` VARCHAR(64) COMMENT 'Voice activity detection identifier',
    `llm_model_id` VARCHAR(32) COMMENT 'LLM identifier',
    `tts_model_id` VARCHAR(32) COMMENT 'TTS model identifier',
    `tts_voice_id` VARCHAR(32) COMMENT 'Voice identifier',
    `mem_model_id` VARCHAR(32) COMMENT 'Memory model identifier',
    `intent_model_id` VARCHAR(32) COMMENT 'Intent model identifier',
    `system_prompt` TEXT COMMENT 'Role setting parameters',
    `lang_code` VARCHAR(10) COMMENT 'Language code',
    `language` VARCHAR(10) COMMENT 'Interaction language',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
    `creator` BIGINT COMMENT 'Creator ID',
    `created_at` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater ID',
    `updated_at` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_agent_user_id` (`user_id`) COMMENT 'Index on the user for quickly finding the agents of a user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent configuration table';

-- Device information table
DROP TABLE IF EXISTS `ai_device`;
CREATE TABLE `ai_device` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Device unique identifier',
    `user_id` BIGINT COMMENT 'Associated user ID',
    `mac_address` VARCHAR(50) COMMENT 'MAC address',
    `last_connected_at` DATETIME COMMENT 'Last connection time',
    `auto_update` TINYINT UNSIGNED DEFAULT 0 COMMENT 'Auto-update switch (0: off, 1: on)',
    `board` VARCHAR(50) COMMENT 'Device hardware model',
    `alias` VARCHAR(64) DEFAULT NULL COMMENT 'Device alias',
    `agent_id` VARCHAR(32) COMMENT 'Agent ID',
    `app_version` VARCHAR(20) COMMENT 'Firmware version',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_device_created_at` (`mac_address`) COMMENT 'Index on the MAC address for quickly finding device information'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Device information table';

-- Voiceprint recognition table
DROP TABLE IF EXISTS `ai_voiceprint`;
CREATE TABLE `ai_voiceprint` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Voiceprint unique identifier',
    `name` VARCHAR(64) COMMENT 'Voiceprint name',
    `user_id` BIGINT COMMENT 'User ID (references the user table)',
    `agent_id` VARCHAR(32) COMMENT 'Associated agent ID',
    `agent_code` VARCHAR(36) COMMENT 'Associated agent code',
    `agent_name` VARCHAR(36) COMMENT 'Associated agent name',
    `description` VARCHAR(255) COMMENT 'Voiceprint description',
    `embedding` LONGTEXT COMMENT 'Voiceprint feature vector (JSON array format)',
    `memory` TEXT COMMENT 'Associated memory data',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
    `creator` BIGINT COMMENT 'Creator ID',
    `created_at` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater ID',
    `updated_at` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Voiceprint recognition table';

-- Conversation history table
DROP TABLE IF EXISTS `ai_chat_history`;
CREATE TABLE `ai_chat_history` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Conversation ID',
    `user_id` BIGINT COMMENT 'User ID',
    `agent_id` VARCHAR(32) DEFAULT NULL COMMENT 'Chat role',
    `device_id` VARCHAR(32) DEFAULT NULL COMMENT 'Device ID',
    `message_count` INT COMMENT 'Message summary',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Conversation history table';

-- Conversation message table
DROP TABLE IF EXISTS `ai_chat_message`;
CREATE TABLE `ai_chat_message` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Conversation record unique identifier',
    `user_id` BIGINT COMMENT 'User unique identifier',
    `chat_id` VARCHAR(64) COMMENT 'Conversation history ID',
    `role` ENUM('user', 'assistant') COMMENT 'Role (user or assistant)',
    `content` TEXT COMMENT 'Conversation content',
    `prompt_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Prompt tokens',
    `total_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Total tokens',
    `completion_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Completion tokens',
    `prompt_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Prompt latency (milliseconds)',
    `total_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Total latency (milliseconds)',
    `completion_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Completion latency (milliseconds)',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Creation time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_chat_message_user_id_chat_id_role` (`user_id`, `chat_id`) COMMENT 'Composite index on user ID, chat session ID and role for quickly retrieving conversation records',
    INDEX `idx_ai_chat_message_created_at` (`create_date`) COMMENT 'Index on the creation time for sorting or retrieving conversation records by time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Conversation message table';
