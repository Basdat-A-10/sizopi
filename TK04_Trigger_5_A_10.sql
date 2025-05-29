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

CREATE OR REPLACE FUNCTION refresh_top_5_adopter()
RETURNS TEXT AS $$
DECLARE
    nama_top VARCHAR;
    kontribusi_top INT;
BEGIN
    SELECT p.nama_depan || ' ' || COALESCE(p.nama_tengah || ' ', '') || p.nama_belakang,
           SUM(a.kontribusi_finansial)
    INTO nama_top, kontribusi_top
    FROM ADOPSI a
    JOIN ADOPTER ad ON ad.id_adopter = a.id_adopter
    JOIN PENGGUNA p ON p.username = ad.username_adopter
    WHERE a.status_pembayaran = 'Lunas'
      AND a.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
    GROUP BY p.nama_depan, p.nama_tengah, p.nama_belakang
    ORDER BY SUM(a.kontribusi_finansial) DESC
    LIMIT 1;

    RETURN FORMAT('SUKSES: Daftar Top 5 Adopter satu tahun terakhir berhasil diperbarui, dengan peringkat pertama dengan nama adopter "%s" berkontribusi sebesar "RP%s"', nama_top, kontribusi_top);
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