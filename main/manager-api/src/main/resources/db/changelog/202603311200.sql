-- Change the data type of the chat content column
ALTER TABLE ai_agent_chat_history MODIFY COLUMN content TEXT COMMENT 'Chat content';
