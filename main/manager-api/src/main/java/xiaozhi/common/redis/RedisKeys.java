package xiaozhi.common.redis;

/**
 * Redis key constants
 * Copyright (c) Renren Open Source All rights reserved.
 * Website: https://www.renren.io
 */
public class RedisKeys {
    /**
     * System parameter key
     */
    public static String getSysParamsKey() {
        return "sys:params";
    }

    /**
     * Verification code key
     */
    public static String getCaptchaKey(String uuid) {
        return "sys:captcha:" + uuid;
    }

    /**
     * Unregistered device verification code key
     */
    public static String getDeviceCaptchaKey(String captcha) {
        return "sys:device:captcha:" + captcha;
    }

    /**
     * User ID key
     */
    public static String getUserIdKey(Long userid) {
        return "sys:username:id:" + userid;
    }

    /**
     * Model name key
     */
    public static String getModelNameById(String id) {
        return "model:name:" + id;
    }

    /**
     * Model configuration key
     */
    public static String getModelConfigById(String id) {
        return "model:data:" + id;
    }

    /**
     * Cache key for the voice name
     */
    public static String getTimbreNameById(String id) {
        return "timbre:name:" + id;
    }

    /**
     * Cache key for the device count
     */
    public static String getAgentDeviceCountById(String id) {
        return "agent:device:count:" + id;
    }

    /**
     * Cache key for the agent's last connection time
     */
    public static String getAgentDeviceLastConnectedAtById(String id) {
        return "agent:device:lastConnected:" + id;
    }

    /**
     * Cache key for the system configuration
     */
    public static String getServerConfigKey() {
        return "server:config";
    }

    /**
     * Cache key for the voice details
     */
    public static String getTimbreDetailsKey(String id) {
        return "timbre:details:" + id;
    }

    /**
     * Cache key for the version number
     */
    public static String getVersionKey() {
        return "sys:version";
    }

    /**
     * OTA firmware ID key
     */
    public static String getOtaIdKey(String uuid) {
        return "ota:id:" + uuid;
    }

    /**
     * OTA firmware download count key
     */
    public static String getOtaDownloadCountKey(String uuid) {
        return "ota:download:count:" + uuid;
    }

    /**
     * Cache key for dictionary data
     */
    public static String getDictDataByTypeKey(String dictType) {
        return "sys:dict:data:" + dictType;
    }

    /**
     * Cache key for agent audio IDs
     */
    public static String getAgentAudioIdKey(String uuid) {
        return "agent:audio:id:" + uuid;
    }

    /**
     * Cache key for SMS verification codes
     */
    public static String getSMSValidateCodeKey(String phone) {
        return "sms:Validate:Code:" + phone;
    }

    /**
     * Cache key for the last SMS verification code send time
     */
    public static String getSMSLastSendTimeKey(String phone) {
        return "sms:Validate:Code:" + phone + ":last_send_time";
    }

    /**
     * Cache key for today's SMS verification code send count
     */
    public static String getSMSTodayCountKey(String phone) {
        return "sms:Validate:Code:" + phone + ":today_count";
    }

    /**
     * Key for the chat history UUID mapping
     */
    public static String getChatHistoryKey(String uuid) {
        return "agent:chat:history:" + uuid;
    }

    /**
     * Cache key for voice cloning audio IDs
     */
    public static String getVoiceCloneAudioIdKey(String uuid) {
        return "voiceClone:audio:id:" + uuid;
    }

    /**
     * Cache key for the knowledge base
     */
    public static String getKnowledgeBaseCacheKey(String datasetId) {
        return "knowledge:base:" + datasetId;
    }

    /**
     * Cache key for the temporary device registration flag
     */
    public static String getTmpRegisterMacKey(String deviceId) {
        return "tmp_register_mac:" + deviceId;
    }

    /**
     * OTA device binding
     */
    public static String getOtaActivationCode(String activationCode) {
        return "ota:activation:code:" + activationCode;
    }

    /**
     * OTA device MAC information lookup
     */
    public static String getOtaDeviceActivationInfo(String deviceId) {
        return "ota:activation:data:" + deviceId;
    }

    /**
     * OTA upload count
     */
    public static String getOtaUploadCountKey(Long username) {
        return "ota:upload:count:" + username;
    }

    /**
     * Device address book cache key
     */
    public static String getAddressBookKey() {
        return "device:address_book:all";
    }

}
