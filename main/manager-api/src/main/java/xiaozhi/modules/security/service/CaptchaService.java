package xiaozhi.modules.security.service;

import java.io.IOException;

import jakarta.servlet.http.HttpServletResponse;

/**
 * Captcha
 * Copyright (c) Renren Open Source All rights reserved.
 * Website: https://www.renren.io
 */
public interface CaptchaService {

    /**
     * Image captcha
     */
    void create(HttpServletResponse response, String uuid) throws IOException;

    /**
     * Validates the captcha
     * 
     * @param uuid   uuid
     * @param code   verification code
     * @param delete whether to delete the captcha
     * @return true: success, false: failure
     */
    boolean validate(String uuid, String code, Boolean delete);

    /**
     * Sends an SMS verification code
     * 
     * @param phone mobile phone
     */
    void sendSMSValidateCode(String phone);

    /**
     * Validates the SMS verification code
     * 
     * @param phone  mobile phone
     * @param code   verification code
     * @param delete whether to delete the captcha
     * @return true: success, false: failure
     */
    boolean validateSMSValidateCode(String phone, String code, Boolean delete);
}
