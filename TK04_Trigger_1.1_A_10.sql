CREATE OR REPLACE FUNCTION SIZOPI.cek_duplikasi_username()
RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM SIZOPI.PENGGUNA
        WHERE username = NEW.username
    ) THEN
        RAISE EXCEPTION 'ERROR: Username "% sudah digunakan, silakan pilih username lain.', NEW.username;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cek_username
BEFORE INSERT ON SIZOPI.PENGGUNA
FOR EACH ROW
EXECUTE FUNCTION SIZOPI.cek_duplikasi_username();
