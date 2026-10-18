-- Add new fields to agent voiceprints
ALTER TABLE ai_agent_voice_print
    ADD COLUMN audio_id VARCHAR(32) NOT NULL COMMENT 'Audio ID';