package xiaozhi.modules.sms.service;

/**
 * Interface definition of SMS service methods
 *
 * @author zjy
 * @since 2025-05-12
 */
public interface SmsService {

    /**
     * Sends a verification code SMS
     * @param phone mobile number
     * @param VerificationCode verification code
     */
    void sendVerificationCodeSms(String phone, String VerificationCode) ;
}
