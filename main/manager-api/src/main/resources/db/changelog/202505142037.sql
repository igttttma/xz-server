update ai_agent_template set system_prompt = replace(system_prompt, 'I am', 'You are');

delete from sys_params where id in (500,501,402);
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (500, 'end_prompt.enable', 'true', 'boolean', 1, 'Whether to enable the closing remarks');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (501, 'end_prompt.prompt', 'Please start with "time really flies" and end this conversation with emotional, reluctant words.', 'string', 1, 'Closing prompt');

INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (402, 'plugins.get_weather.api_host', 'mj7p3y7naa.re.qweatherapi.com', 'string', 1, 'Developer API host');