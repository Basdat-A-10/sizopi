CREATE OR REPLACE FUNCTION sync_total_kontribusi_adopter(p_id_adopter UUID)
RETURNS TEXT AS $$
DECLARE
    total INT;
    nama_pengguna VARCHAR;
BEGIN
    SELECT COALESCE(SUM(kontribusi_finansial), 0)
    INTO total
    FROM ADOPSI
    WHERE id_adopter = p_id_adopter AND status_pembayaran = 'Lunas';

    UPDATE ADOPTER
    SET total_kontribusi = total
    WHERE id_adopter = p_id_adopter;

    SELECT nama_depan || ' ' || COALESCE(nama_tengah || ' ', '') || nama_belakang
    INTO nama_pengguna
    FROM PENGGUNA
    WHERE username = (SELECT username_adopter FROM ADOPTER WHERE id_adopter = p_id_adopter);

    -- Return message
    RETURN FORMAT('SUKSES: Total kontribusi adopter "%s" telah diperbarui.', nama_pengguna);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION trigger_sync_total_kontribusi()
RETURNS TRIGGER AS $$
DECLARE
    message TEXT;
BEGIN
    message := sync_total_kontribusi_adopter(NEW.id_adopter);
    RAISE NOTICE 'TRIGGER_MESSAGE: %', message;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_total_kontribusi
AFTER INSERT OR UPDATE OF status_pembayaran ON ADOPSI
FOR EACH ROW
WHEN (NEW.status_pembayaran = 'Lunas')
EXECUTE FUNCTION trigger_sync_total_kontribusi();