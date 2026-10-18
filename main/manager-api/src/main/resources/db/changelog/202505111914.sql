-- Add the chat history configuration field
ALTER TABLE `ai_agent` 
ADD COLUMN `chat_history_conf` tinyint NOT NULL DEFAULT 0 COMMENT 'Chat history configuration (0: do not record, 1: record text only, 2: record text and audio)' AFTER `system_prompt`;

ALTER TABLE `ai_agent_template` 
ADD COLUMN `chat_history_conf` tinyint NOT NULL DEFAULT 0 COMMENT 'Chat history configuration (0: do not record, 1: record text only, 2: record text and audio)' AFTER `system_prompt`;