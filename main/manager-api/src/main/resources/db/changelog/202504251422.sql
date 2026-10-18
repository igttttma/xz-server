-- Add server.ota to configure the OTA address

delete from `sys_params` where id = 100;
delete from `sys_params` where id = 101;

delete from `sys_params` where id = 106;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (106, 'server.websocket', 'null', 'string', 1, 'WebSocket address; separate multiple values with ;');

delete from `sys_params` where id = 107;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (107, 'server.ota', 'null', 'string', 1, 'OTA address');


-- Add the firmware information table
CREATE TABLE IF NOT EXISTS `ai_ota` (
  `id` varchar(32) NOT NULL COMMENT 'ID',
  `firmware_name` varchar(100) DEFAULT NULL COMMENT 'Firmware name',
  `type` varchar(50) DEFAULT NULL COMMENT 'Firmware type',
  `version` varchar(50) DEFAULT NULL COMMENT 'Version number',
  `size` bigint DEFAULT NULL COMMENT 'File size (bytes)',
  `remark` varchar(500) DEFAULT NULL COMMENT 'Remark / description',
  `firmware_path` varchar(255) DEFAULT NULL COMMENT 'Firmware path',
  `sort` int unsigned DEFAULT '0' COMMENT 'Sort order',
  `updater` bigint DEFAULT NULL COMMENT 'Updater',
  `update_date` datetime DEFAULT NULL COMMENT 'Update time',
  `creator` bigint DEFAULT NULL COMMENT 'Creator',
  `create_date` datetime DEFAULT NULL COMMENT 'Creation time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Firmware information table';

update ai_device set auto_update = 1;
