DROP TRIGGER IF EXISTS trigger_check_rotasi_pelatih_fix ON JADWAL_PENUGASAN;
DROP TRIGGER IF EXISTS trigger_check_rotasi_pelatih ON JADWAL_PENUGASAN;
DROP TRIGGER IF EXISTS trigger_rotation_check ON JADWAL_PENUGASAN;

CREATE OR REPLACE FUNCTION check_and_rotate_trainer()
RETURNS TRIGGER AS $$
DECLARE
    first_assignment TIMESTAMP;
    days_difference INTEGER;
    nama_pelatih TEXT;
    rotation_message TEXT;
BEGIN
    SELECT MIN(tgl_penugasan) INTO first_assignment
    FROM JADWAL_PENUGASAN
    WHERE username_lh = NEW.username_lh
    AND nama_atraksi = NEW.nama_atraksi
    AND tgl_penugasan < NEW.tgl_penugasan;
    
    IF first_assignment IS NOT NULL THEN
        days_difference := EXTRACT(DAY FROM (NEW.tgl_penugasan - first_assignment));
        
        IF days_difference > 90 THEN
            SELECT TRIM(CONCAT(P.nama_depan, ' ',
                   COALESCE(P.nama_tengah || ' ', ''),
                   P.nama_belakang)) INTO nama_pelatih
            FROM PENGGUNA P
            WHERE P.username = NEW.username_lh;
            
            rotation_message := 'SUKSES: Pelatih "' || COALESCE(nama_pelatih, NEW.username_lh) ||
                               '" telah bertugas lebih dari 3 bulan (' || days_difference || ' hari) di atraksi "' || NEW.nama_atraksi ||
                               '" dan perlu diganti dengan pelatih baru.';
            
            INSERT INTO rotation_log (username_lh, nama_atraksi, message)
            VALUES (NEW.username_lh, NEW.nama_atraksi, rotation_message);
            
            RAISE NOTICE '%', rotation_message;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_rotation_check AFTER INSERT ON JADWAL_PENUGASAN FOR EACH ROW EXECUTE FUNCTION check_and_rotate_trainer();

CREATE OR REPLACE FUNCTION simulate_old_assignment(
    p_trainer VARCHAR(50),
    p_atraksi VARCHAR(100),
    p_days_ago INTEGER
)
RETURNS TEXT AS $$
DECLARE
    old_date TIMESTAMP;
BEGIN
    old_date := CURRENT_TIMESTAMP - (p_days_ago || ' days')::INTERVAL;
    
    INSERT INTO JADWAL_PENUGASAN (username_lh, nama_atraksi, tgl_penugasan)
    VALUES (p_trainer, p_atraksi, old_date)
    ON CONFLICT (username_lh, tgl_penugasan) DO NOTHING;
    
    RETURN 'Old assignment created: ' || p_trainer || ' at ' || p_atraksi || ' (' || p_days_ago || ' days ago)';
END;
$$ LANGUAGE plpgsql;