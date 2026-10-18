-- liquibase formatted sql

-- Insert a new hass_state plugin record (merging the configuration fields of get_state)
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_STATE',
        'Plugin',
        'hass_state',
        'HomeAssistant Device Control',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'base_url',
                        'type', 'string',
                        'label', 'HA server address',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.base_url')
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'HA API access token',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.api_key')
                ),
                JSON_OBJECT(
                        'key', 'devices',
                        'type', 'array',
                        'label', 'Device list (name,entity ID;...)',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.devices')
                )
        ),
        50, 0, NOW(), 0, NOW());

-- Migrate configured agents: change references from HA_GET_STATE to HA_STATE (keep parameters)
UPDATE ai_agent_plugin_mapping
SET plugin_id = 'SYSTEM_PLUGIN_HA_STATE'
WHERE plugin_id = 'SYSTEM_PLUGIN_HA_GET_STATE';

-- HA_SET_STATE never had configuration fields (fields=[]), so delete its mapping directly
DELETE FROM ai_agent_plugin_mapping
WHERE plugin_id = 'SYSTEM_PLUGIN_HA_SET_STATE';

-- Delete the old plugin definitions
DELETE FROM ai_model_provider
WHERE id IN ('SYSTEM_PLUGIN_HA_GET_STATE', 'SYSTEM_PLUGIN_HA_SET_STATE');
