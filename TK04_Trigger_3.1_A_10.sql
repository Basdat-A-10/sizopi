/*
=============================================================================
TK04 - TRIGGER 3.1: SINKRONISASI REKAM MEDIS DAN PENJADWALAN KESEHATAN
=============================================================================

Trigger ini menangani sinkronisasi antara rekam medis dan penjadwalan 
pemeriksaan kesehatan satwa. Setelah memasukkan data rekam medis baru, 
jika status kesehatan hewan yang baru dimasukkan adalah "Sakit", sistem 
otomatis mengubah tanggal pemeriksaan selanjutnya (jika ada) yang sama 
atau paling dekat setelah tanggal pemeriksaan rekam medis yang baru 
dimasukkan untuk hewan tersebut menjadi 7 hari dari tanggal pemeriksaan 
rekam medis yang baru dimasukkan. Jika tidak ditemukan tanggal pemeriksaan 
selanjutnya yang memenuhi syarat, buat jadwal pemeriksaan baru dengan 
aturan tanggal pemeriksaan selanjutnya yang sama.

FITUR YANG DIIMPLEMENTASI:
1. Sinkronisasi Rekam Medis dan Penjadwalan Pemeriksaan Kesehatan
   - Trigger otomatis ketika rekam medis baru ditambahkan
   - Update jadwal jika status kesehatan "Sakit"
   - Generate jadwal baru jika diperlukan
   
2. Pembersihan Jadwal ketika Rekam Medis Dihapus
   - Otomatis menghapus jadwal terkait ketika rekam medis dihapus
   - Mencegah jadwal yatim (orphaned schedules)

=============================================================================
*/

SET search_path TO SIZOPI;

-- Hapus trigger dan fungsi yang ada untuk sinkronisasi rekam medis
DROP TRIGGER IF EXISTS trigger_sync_medical_schedule ON CATATAN_MEDIS;
DROP TRIGGER IF EXISTS trigger_cleanup_medical_schedule ON CATATAN_MEDIS;
DROP FUNCTION IF EXISTS sync_medical_record_schedule();
DROP FUNCTION IF EXISTS cleanup_medical_record_schedule();

/*
=============================================================================
FUNGSI 1: SINKRONISASI REKAM MEDIS DAN JADWAL PEMERIKSAAN
=============================================================================
*/
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
        
        -- Hapus jadwal yang ada setelah tanggal pemeriksaan, mencegah duplicate key
        DELETE FROM JADWAL_PEMERIKSAAN_KESEHATAN
        WHERE id_hewan = NEW.id_hewan
        AND tgl_pemeriksaan_selanjutnya >= NEW.tanggal_pemeriksaan;
        
        -- Selalu buat jadwal baru (agar tidak ada risiko duplicate)
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
            
            -- Buat jadwal baru (aman karena sudah dihapus yang conflict)
            INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN
                (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES
                (NEW.id_hewan, next_checkup_date, last_freq);
            
            -- Output pesan sukses sesuai format yang diminta soal
            RAISE NOTICE 'TRIGGER_MESSAGE: SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui karena status kesehatan "Sakit".', 
                animal_name;
            -- Backup: Set session variable
            PERFORM set_config('custom.last_trigger_message', format('SUKSES: Jadwal pemeriksaan hewan "%s" telah diperbarui karena status kesehatan "Sakit".', animal_name), false);
        END;
    END IF;
    
    -- Update status kesehatan hewan
    UPDATE HEWAN
    SET status_kesehatan = NEW.status_kesehatan
    WHERE id = NEW.id_hewan;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

/*
=============================================================================
FUNGSI 2: PEMBERSIHAN JADWAL KETIKA REKAM MEDIS DIHAPUS
=============================================================================
*/
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
        -- Backup: Set session variable
        PERFORM set_config('custom.last_trigger_message', format('SUKSES: %s jadwal pemeriksaan untuk hewan "%s" telah dihapus karena rekam medis terkait dihapus.', deleted_count, animal_name), false);
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

/*
=============================================================================
TRIGGER DEFINITIONS - SINKRONISASI REKAM MEDIS DAN PENJADWALAN
=============================================================================
*/

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

