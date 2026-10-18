-- Update the EdgeTTS provider and add speech rate, pitch and volume settings
UPDATE `ai_model_provider`
SET fields = '[{"key":"voice","label":"Voice","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"rate","label":"Speech Rate (-100~100)","type":"number"},{"key":"volume","label":"Volume (0~100)","type":"number"},{"key":"pitch","label":"Pitch (-100~100)","type":"number"}]'
WHERE id = 'SYSTEM_TTS_edge';

UPDATE `ai_model_config` SET
`remark` = 'EdgeTTS configuration:
1. Uses the Microsoft Edge TTS service
2. Supports multiple languages and voices
3. Free to use, no registration required
4. Network connection required
5. Output files are saved in the tmp/ directory
6. Speech rate: -100~100, 0 is normal speed
7. Volume: 0~100, 50 is normal volume
8. Pitch: -100~100, 0 is normal pitch' WHERE `id` = 'TTS_EdgeTTS';
