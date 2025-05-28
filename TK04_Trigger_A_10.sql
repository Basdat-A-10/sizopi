SET search_path TO SIZOPI;

-- Hapus trigger yang ada
DROP TRIGGER IF EXISTS trigger_sync_medical_schedule ON CATATAN_MEDIS;
DROP TRIGGER IF EXISTS trigger_cleanup_medical_schedule ON CATATAN_MEDIS;
DROP TRIGGER IF EXISTS trigger_auto_generate_schedules ON JADWAL_PEMERIKSAAN_KESEHATAN;
DROP TRIGGER IF EXISTS trigger_update_frequency_schedules ON JADWAL_PEMERIKSAAN_KESEHATAN;
DROP FUNCTION IF EXISTS sync_medical_record_schedule();
DROP FUNCTION IF EXISTS cleanup_medical_record_schedule();
DROP FUNCTION IF EXISTS auto_generate_schedules();
DROP FUNCTION IF EXISTS update_frequency_schedules();

-- Fungsi untuk sinkronisasi catatan medis dan jadwal
CREATE OR REPLACE FUNCTION sync_medical_record_schedule()
RETURNS TRIGGER AS $$
DECLARE
    next_checkup_date DATE;
    animal_name VARCHAR(100);
BEGIN
    -- Ambil nama hewan untuk log
    SELECT nama INTO animal_name FROM HEWAN WHERE id = NEW.id_hewan;
    
    -- Hanya dijalankan jika status kesehatan adalah "Sakit"
    IF NEW.status_kesehatan = 'Sakit' THEN
        -- Set jadwal 7 hari dari tanggal pemeriksaan
        next_checkup_date := NEW.tanggal_pemeriksaan + INTERVAL '7 days';
        
        -- Periksa apakah ada jadwal pemeriksaan setelah tanggal ini
        UPDATE JADWAL_PEMERIKSAAN_KESEHATAN
        SET tgl_pemeriksaan_selanjutnya = next_checkup_date
        WHERE id_hewan = NEW.id_hewan
        AND tgl_pemeriksaan_selanjutnya >= NEW.tanggal_pemeriksaan;
        
        -- Jika tidak ada jadwal yang diupdate, buat jadwal baru
        IF NOT FOUND THEN
            -- Cari frekuensi terakhir untuk hewan ini
            DECLARE
                last_freq INT;
            BEGIN
                SELECT freq_pemeriksaan_rutin INTO last_freq
                FROM JADWAL_PEMERIKSAAN_KESEHATAN
                WHERE id_hewan = NEW.id_hewan
                ORDER BY tgl_pemeriksaan_selanjutnya DESC
                LIMIT 1;
                
                -- Jika tidak ada, gunakan default 3 bulan
                IF last_freq IS NULL THEN
                    last_freq := 3;
                END IF;
                
                -- Buat jadwal baru dengan frekuensi yang ada
                INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN
                    (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                VALUES
                    (NEW.id_hewan, next_checkup_date, last_freq);
                
                -- Gunakan format pesan yang benar
                RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui karena status kesehatan "Sakit".', 
                    animal_name;
                    
                -- Trigger pembuatan jadwal lain dalam setahun
                PERFORM auto_generate_schedules(NEW.id_hewan, next_checkup_date, last_freq);
            END;
        ELSE
            -- Format pesan untuk update jadwal
            RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui karena status kesehatan "Sakit".', 
                animal_name;
        END IF;
    END IF;
    
    -- Update status kesehatan hewan
    UPDATE HEWAN
    SET status_kesehatan = NEW.status_kesehatan
    WHERE id = NEW.id_hewan;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Fungsi untuk membersihkan jadwal ketika rekam medis dihapus
CREATE OR REPLACE FUNCTION cleanup_medical_record_schedule()
RETURNS TRIGGER AS $$
DECLARE
    animal_name VARCHAR(100);
    deleted_count INT;
BEGIN
    -- Ambil nama hewan untuk log
    SELECT nama INTO animal_name FROM HEWAN WHERE id = OLD.id_hewan;
    
    -- Hapus semua jadwal pemeriksaan untuk hewan ini yang dibuat setelah tanggal rekam medis yang dihapus
    DELETE FROM JADWAL_PEMERIKSAAN_KESEHATAN
    WHERE id_hewan = OLD.id_hewan
    AND tgl_pemeriksaan_selanjutnya >= OLD.tanggal_pemeriksaan + INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Kirim pesan jika ada jadwal yang dihapus
    IF deleted_count > 0 THEN
        RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: % jadwal pemeriksaan untuk hewan "%s" telah dihapus karena rekam medis terkait dihapus.', 
            deleted_count, animal_name;
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Fungsi untuk menghasilkan jadwal pemeriksaan secara otomatis
CREATE OR REPLACE FUNCTION auto_generate_schedules(p_id_hewan UUID, p_start_date DATE, p_freq_months INT)
RETURNS VOID AS $$
DECLARE
    next_date DATE := p_start_date;
    curr_date DATE := CURRENT_DATE;
    year_end DATE := (EXTRACT(YEAR FROM p_start_date) || '-12-31')::DATE;
    animal_name VARCHAR(100);
    schedule_count INT := 0;
BEGIN
    -- Set flag untuk mencegah trigger rekursif
    PERFORM set_config('sizopi.auto_generating', 'true', true);
    
    -- Ambil nama hewan
    SELECT nama INTO animal_name FROM HEWAN WHERE id = p_id_hewan;
    
    -- Pastikan frekuensi valid
    IF p_freq_months IS NULL OR p_freq_months <= 0 THEN
        p_freq_months := 3; -- Default 3 bulan
    END IF;
    
    -- Generate jadwal untuk satu tahun
    WHILE next_date <= year_end AND schedule_count < 12 LOOP
        -- Tambahkan bulan sesuai frekuensi
        next_date := next_date + (p_freq_months || ' months')::INTERVAL;
        
        -- Jika tanggal masih dalam tahun yang sama
        IF next_date <= year_end THEN
            -- Cek apakah jadwal sudah ada
            IF NOT EXISTS (
                SELECT 1 
                FROM JADWAL_PEMERIKSAAN_KESEHATAN 
                WHERE id_hewan = p_id_hewan 
                AND tgl_pemeriksaan_selanjutnya = next_date
            ) THEN
                -- Insert jadwal baru
                INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN 
                    (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                VALUES 
                    (p_id_hewan, next_date, p_freq_months);
                
                schedule_count := schedule_count + 1;
            END IF;
        END IF;
    END LOOP;
    
    -- Reset flag
    PERFORM set_config('sizopi.auto_generating', 'false', true);
    
    -- Kirim pesan sukses jika ada jadwal yang dibuat
    IF schedule_count > 0 THEN
        RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: % jadwal pemeriksaan rutin hewan "%s" telah ditambahkan sesuai frekuensi %s bulan.', 
            schedule_count, animal_name, p_freq_months;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger untuk pembuatan otomatis jadwal ketika rekam medis dibuat
CREATE TRIGGER trigger_sync_medical_schedule
AFTER INSERT ON CATATAN_MEDIS
FOR EACH ROW
EXECUTE FUNCTION sync_medical_record_schedule();

-- Trigger untuk membersihkan jadwal ketika rekam medis dihapus
CREATE TRIGGER trigger_cleanup_medical_schedule
AFTER DELETE ON CATATAN_MEDIS
FOR EACH ROW
EXECUTE FUNCTION cleanup_medical_record_schedule();

-- Trigger untuk auto-generate jadwal ketika jadwal baru dibuat manual
CREATE OR REPLACE FUNCTION trigger_auto_generate_schedules_func()
RETURNS TRIGGER AS $$
DECLARE
    animal_name VARCHAR(100);
BEGIN
    IF current_setting('sizopi.auto_generating', true) = 'true' THEN
        RETURN NEW;
    END IF;
    
    SELECT nama INTO animal_name FROM HEWAN WHERE id = NEW.id_hewan;
    
    -- Generate jadwal untuk tahun ini
    PERFORM auto_generate_schedules(NEW.id_hewan, NEW.tgl_pemeriksaan_selanjutnya, NEW.freq_pemeriksaan_rutin);
    
    RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan rutin hewan "%s" telah ditambahkan sesuai frekuensi.', 
        animal_name;
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_generate_schedules
AFTER INSERT ON JADWAL_PEMERIKSAAN_KESEHATAN
FOR EACH ROW
EXECUTE FUNCTION trigger_auto_generate_schedules_func();

-- Fungsi untuk regenerate jadwal ketika frekuensi diubah
CREATE OR REPLACE FUNCTION update_frequency_schedules()
RETURNS TRIGGER AS $$
DECLARE
    animal_name VARCHAR(100);
    earliest_date DATE;
    deleted_count INT;
    schedule_count INT := 0;
BEGIN
    -- Jangan eksekusi jika sedang dalam mode auto-generation
    IF current_setting('sizopi.auto_generating', true) = 'true' THEN
        RETURN NEW;
    END IF;
    
    -- Hanya jalankan jika frekuensi berubah
    IF OLD.freq_pemeriksaan_rutin = NEW.freq_pemeriksaan_rutin THEN
        RETURN NEW;
    END IF;
    
    SELECT nama INTO animal_name FROM HEWAN WHERE id = NEW.id_hewan;
    
    -- Flag untuk mencegah trigger rekursif
    PERFORM set_config('sizopi.auto_generating', 'true', true);
    
    -- Cari tanggal jadwal paling awal untuk hewan ini
    SELECT MIN(tgl_pemeriksaan_selanjutnya) INTO earliest_date
    FROM JADWAL_PEMERIKSAAN_KESEHATAN
    WHERE id_hewan = NEW.id_hewan;
    
    -- Hapus SEMUA jadwal untuk hewan ini kecuali yang paling awal
    DELETE FROM JADWAL_PEMERIKSAAN_KESEHATAN
    WHERE id_hewan = NEW.id_hewan 
    AND tgl_pemeriksaan_selanjutnya > earliest_date;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Update frekuensi pada SEMUA jadwal yang tersisa untuk hewan ini
    UPDATE SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
    SET freq_pemeriksaan_rutin = NEW.freq_pemeriksaan_rutin
    WHERE id_hewan = NEW.id_hewan;
    
    -- Generate ulang jadwal berdasarkan frekuensi baru
    PERFORM auto_generate_schedules(NEW.id_hewan, earliest_date, NEW.freq_pemeriksaan_rutin);
    
    -- Reset flag
    PERFORM set_config('sizopi.auto_generating', 'false', true);
    
    RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui sesuai frekuensi baru %s bulan.', 
        animal_name, NEW.freq_pemeriksaan_rutin;
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger untuk regenerate jadwal ketika frekuensi diubah
CREATE TRIGGER trigger_update_frequency_schedules
AFTER UPDATE ON JADWAL_PEMERIKSAAN_KESEHATAN
FOR EACH ROW
EXECUTE FUNCTION update_frequency_schedules();