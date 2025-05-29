CREATE OR REPLACE FUNCTION SIZOPI.verify_login_credentials()
RETURNS TRIGGER AS $$
DECLARE
    user_exists BOOLEAN := FALSE;
    stored_password VARCHAR(255);
    input_email VARCHAR(255);
    input_password VARCHAR(255);
BEGIN
    input_email := NEW.email;
    
    -- Cek apakah user dengan email tersebut ada
    SELECT EXISTS(
        SELECT 1 FROM SIZOPI.PENGGUNA WHERE email = input_email
    ) INTO user_exists;
    
    IF NOT user_exists THEN
        -- Update message untuk user tidak ditemukan
        NEW.success := FALSE;
        NEW.message := 'Username atau password salah, silakan coba lagi.';
        RETURN NEW;
    END IF;
    
    -- Jika NEW.success = FALSE, berarti password salah (dari aplikasi)
    IF NEW.success = FALSE THEN
        NEW.message := 'Username atau password salah, silakan coba lagi.';
    ELSE
        NEW.message := 'Login berhasil.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Buat trigger
DROP TRIGGER IF EXISTS trigger_verify_login ON SIZOPI.LOGIN_LOG;

CREATE TRIGGER trigger_verify_login
    BEFORE INSERT ON SIZOPI.LOGIN_LOG
    FOR EACH ROW
    EXECUTE FUNCTION SIZOPI.verify_login_credentials();