-- 1. Drop existing triggers
DROP TRIGGER IF EXISTS trigger_rotation_check ON JADWAL_PENUGASAN;
DROP TRIGGER IF EXISTS trigger_simple_rotation ON JADWAL_PENUGASAN;
DROP TRIGGER IF EXISTS trigger_debug_rotation ON JADWAL_PENUGASAN;

-- 2. Clean rotation function
CREATE OR REPLACE FUNCTION SIZOPI.check_trainer_rotation()
RETURNS TRIGGER AS $$
DECLARE
    days_worked INTEGER;
    first_assignment TIMESTAMP;
    trainer_name TEXT;
    new_trainer VARCHAR(50);
    new_trainer_name TEXT;
BEGIN
    -- Cari assignment pertama trainer ini di atraksi yang sama
    SELECT MIN(tgl_penugasan) INTO first_assignment
    FROM JADWAL_PENUGASAN
    WHERE username_lh = NEW.username_lh
    AND nama_atraksi = NEW.nama_atraksi
    AND tgl_penugasan < NEW.tgl_penugasan;
    
    -- Jika ada assignment sebelumnya, hitung hari kerja
    IF first_assignment IS NOT NULL THEN
        days_worked := EXTRACT(DAY FROM (NEW.tgl_penugasan - first_assignment));
        
        -- Jika lebih dari 90 hari, lakukan rotasi
        IF days_worked > 90 THEN
            -- Ambil nama trainer lama
            SELECT TRIM(CONCAT(P.nama_depan, ' ',
                   COALESCE(P.nama_tengah || ' ', ''),
                   P.nama_belakang)) INTO trainer_name
            FROM PENGGUNA P
            WHERE P.username = NEW.username_lh;
            
            -- Log rotasi
            INSERT INTO rotation_log (username_lh, nama_atraksi, message)
            VALUES (NEW.username_lh, NEW.nama_atraksi, 
                   'SUKSES: Pelatih "' || COALESCE(trainer_name, NEW.username_lh) || 
                   '" telah bertugas lebih dari 3 bulan (' || days_worked || ' hari) di atraksi "' || 
                   NEW.nama_atraksi || '" dan perlu diganti dengan pelatih baru.');
            
            -- Hapus semua assignment lama trainer ini di atraksi ini
            DELETE FROM JADWAL_PENUGASAN 
            WHERE username_lh = NEW.username_lh 
            AND nama_atraksi = NEW.nama_atraksi;
            
            -- Cari trainer pengganti yang available
            SELECT PH.username_lh INTO new_trainer
            FROM PELATIH_HEWAN PH
            WHERE PH.username_lh != NEW.username_lh
            AND NOT EXISTS (
                SELECT 1 FROM JADWAL_PENUGASAN JP 
                WHERE JP.username_lh = PH.username_lh 
                AND JP.tgl_penugasan = NEW.tgl_penugasan
            )
            ORDER BY RANDOM()
            LIMIT 1;
            
            -- Jika ada trainer pengganti
            IF new_trainer IS NOT NULL THEN
                -- Ambil nama trainer baru
                SELECT TRIM(CONCAT(P.nama_depan, ' ',
                       COALESCE(P.nama_tengah || ' ', ''),
                       P.nama_belakang)) INTO new_trainer_name
                FROM PENGGUNA P
                WHERE P.username = new_trainer;
                
                -- Insert assignment baru dengan trainer pengganti
                INSERT INTO JADWAL_PENUGASAN (username_lh, nama_atraksi, tgl_penugasan)
                VALUES (new_trainer, NEW.nama_atraksi, NEW.tgl_penugasan);
                
                -- Log penggantian
                INSERT INTO rotation_log (username_lh, nama_atraksi, message)
                VALUES (new_trainer, NEW.nama_atraksi, 
                       'INFO: Trainer baru "' || COALESCE(new_trainer_name, new_trainer) || 
                       '" ditugaskan menggantikan "' || COALESCE(trainer_name, NEW.username_lh) || 
                       '" di atraksi "' || NEW.nama_atraksi || '".');
                
                -- Batalkan INSERT original karena sudah diganti
                RETURN NULL;
            ELSE
                -- Tidak ada trainer pengganti
                INSERT INTO rotation_log (username_lh, nama_atraksi, message)
                VALUES (NEW.username_lh, NEW.nama_atraksi, 
                       'WARNING: Rotasi diperlukan untuk "' || COALESCE(trainer_name, NEW.username_lh) || 
                       '" tapi tidak ada trainer pengganti yang tersedia.');
                
                -- Lanjutkan dengan trainer lama
                RETURN NEW;
            END IF;
        END IF;
    END IF;
    
    -- Jika tidak perlu rotasi, lanjutkan normal
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Create trigger
CREATE TRIGGER trigger_trainer_rotation
    BEFORE INSERT ON JADWAL_PENUGASAN
    FOR EACH ROW
    EXECUTE FUNCTION SIZOPI.check_trainer_rotation();

-- 4. Helper function untuk testing
CREATE OR REPLACE FUNCTION SIZOPI.create_old_assignment(
    trainer_username VARCHAR(50),
    atraksi_name VARCHAR(100),
    days_ago INTEGER DEFAULT 100
)
RETURNS TEXT AS $$
DECLARE
    old_date TIMESTAMP;
BEGIN
    old_date := CURRENT_TIMESTAMP - (days_ago || ' days')::INTERVAL;
    
    -- Hapus assignment existing untuk trainer ini di atraksi ini
    DELETE FROM JADWAL_PENUGASAN 
    WHERE username_lh = trainer_username AND nama_atraksi = atraksi_name;
    
    -- Insert assignment lama
    INSERT INTO JADWAL_PENUGASAN (username_lh, nama_atraksi, tgl_penugasan)
    VALUES (trainer_username, atraksi_name, old_date);
    
    RETURN 'Assignment created: ' || trainer_username || ' at ' || atraksi_name || 
           ' (' || days_ago || ' days ago: ' || old_date || ')';
END;
$$ LANGUAGE plpgsql;