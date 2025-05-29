/*
=============================================================================
TK04 - TRIGGER 3.2: PENAMBAHAN JADWAL PEMERIKSAAN SESUAI FREKUENSI
=============================================================================

Trigger ini menangani penambahan jadwal pemeriksaan sesuai dengan frekuensi 
yang telah ditentukan. Ketika dibuat jadwal pemeriksaan baru, perlu 
ditambahkan juga data jadwal pemeriksaan lainnya secara otomatis dalam 
tahun yang sama sesuai dengan frekuensi pemeriksaan rutin hewan. Dimana 
penambahan jadwal otomatis tersebut disesuaikan dengan frekuensi pemeriksaan 
rutin hewan.

FITUR YANG DIIMPLEMENTASI:
1. Auto-Generate Jadwal Pemeriksaan Sesuai Frekuensi
   - Otomatis membuat jadwal berdasarkan frekuensi yang ditentukan
   - Generate untuk satu tahun penuh
   - Mencegah duplikasi jadwal
   
2. Update Jadwal ketika Frekuensi Berubah
   - Regenerate ulang semua jadwal ketika frekuensi diubah
   - Membersihkan jadwal lama dan membuat yang baru
   - Mempertahankan jadwal paling awal sebagai referensi

=============================================================================
*/

SET search_path TO SIZOPI;

-- Hapus trigger dan fungsi yang ada untuk auto-generate jadwal
DROP TRIGGER IF EXISTS trigger_auto_generate_schedules ON JADWAL_PEMERIKSAAN_KESEHATAN;
DROP TRIGGER IF EXISTS trigger_update_frequency_schedules ON JADWAL_PEMERIKSAAN_KESEHATAN;
DROP FUNCTION IF EXISTS auto_generate_schedules(UUID, DATE, INT);
DROP FUNCTION IF EXISTS trigger_auto_generate_schedules_func();
DROP FUNCTION IF EXISTS update_frequency_schedules();

/*
=============================================================================
FUNGSI 1: AUTO-GENERATE JADWAL PEMERIKSAAN SESUAI FREKUENSI
=============================================================================
*/
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
    
    -- Kirim pesan sukses jika ada jadwal yang dibuat sesuai format soal
    IF schedule_count > 0 THEN
        RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan rutin hewan "%s" telah ditambahkan sesuai frekuensi.', 
            animal_name;
        -- Backup: Set session variable
        PERFORM set_config('custom.last_trigger_message', format('SUKSES: Jadwal pemeriksaan rutin hewan "%s" telah ditambahkan sesuai frekuensi.', animal_name), false);
    END IF;
END;
$$ LANGUAGE plpgsql;

/*
=============================================================================
FUNGSI 2: TRIGGER FUNCTION UNTUK AUTO-GENERATE JADWAL
=============================================================================
*/
CREATE OR REPLACE FUNCTION trigger_auto_generate_schedules_func()
RETURNS TRIGGER AS $$
DECLARE
    animal_name VARCHAR(100);
BEGIN
    -- Jangan eksekusi jika sedang dalam mode auto-generation
    IF current_setting('sizopi.auto_generating', true) = 'true' THEN
        RETURN NEW;
    END IF;
    
    SELECT nama INTO animal_name FROM HEWAN WHERE id = NEW.id_hewan;
    
    -- Generate jadwal untuk tahun ini
    PERFORM auto_generate_schedules(NEW.id_hewan, NEW.tgl_pemeriksaan_selanjutnya, NEW.freq_pemeriksaan_rutin);
    
    -- Output pesan sesuai format soal
    RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan rutin hewan "%s" telah ditambahkan sesuai frekuensi.', 
        animal_name;
    -- Backup: Set session variable
    PERFORM set_config('custom.last_trigger_message', format('SUKSES: Jadwal pemeriksaan rutin hewan "%s" telah ditambahkan sesuai frekuensi.', animal_name), false);
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*
=============================================================================
FUNGSI 3: UPDATE JADWAL KETIKA FREKUENSI BERUBAH
=============================================================================
*/
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
    
    -- Output pesan sesuai format soal
    RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui sesuai frekuensi baru %s bulan.', 
        animal_name, NEW.freq_pemeriksaan_rutin;
    -- Backup: Set session variable
    PERFORM set_config('custom.last_trigger_message', format('SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui sesuai frekuensi baru %s bulan.', animal_name, NEW.freq_pemeriksaan_rutin), false);
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*
=============================================================================
TRIGGER DEFINITIONS - AUTO-GENERATE JADWAL SESUAI FREKUENSI
=============================================================================
*/

-- Trigger untuk auto-generate jadwal ketika jadwal baru dibuat manual
CREATE TRIGGER trigger_auto_generate_schedules
AFTER INSERT ON JADWAL_PEMERIKSAAN_KESEHATAN
FOR EACH ROW
EXECUTE FUNCTION trigger_auto_generate_schedules_func();

-- Trigger untuk regenerate jadwal ketika frekuensi diubah
CREATE TRIGGER trigger_update_frequency_schedules
AFTER UPDATE ON JADWAL_PEMERIKSAAN_KESEHATAN
FOR EACH ROW
EXECUTE FUNCTION update_frequency_schedules();
