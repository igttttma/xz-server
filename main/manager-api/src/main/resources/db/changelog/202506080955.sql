-- Enable wake word acceleration in the Control Panel
update `sys_params` set param_value = 'Hi XiaoZhi;Hello XiaoZhi;Xiao Ai;Hi XiaoXin;Hi XiaoXin;Xiao Mei;Xiao Long;Meow Meow;Xiao Bin;Xiao Bing;Hey there' where param_code = 'wakeup_words';
update `sys_params` set param_value = 'true' where param_code = 'enable_wakeup_words_response_cache';
