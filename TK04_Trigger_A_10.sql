-- Set search path untuk schema SIZOPI
SET search_path TO SIZOPI;

-- Hapus semua trigger terlebih dahulu untuk memastikan tidak ada konflik
DROP TRIGGER IF EXISTS trigger_sync_medical_schedule ON CATATAN_MEDIS;
DROP TRIGGER IF EXISTS trigger_auto_schedule_checkup ON JADWAL_PEMERIKSAAN_KESEHATAN;
DROP TRIGGER IF EXISTS trigger_update_health_status ON CATATAN_MEDIS;
DROP TRIGGER IF EXISTS trigger_validate_feeding ON PAKAN;
DROP TRIGGER IF EXISTS trigger_auto_assign_caretaker ON PAKAN;
DROP FUNCTION IF EXISTS sync_medical_record_schedule();
DROP FUNCTION IF EXISTS auto_schedule_next_checkup();
DROP FUNCTION IF EXISTS update_animal_health_status();
DROP FUNCTION IF EXISTS validate_feeding_schedule();
DROP FUNCTION IF EXISTS auto_assign_caretaker();

-- =============================================================================
-- TRIGGER 1: Sinkronisasi Rekam Medis dan Penjadwalan Pemeriksaan Kesehatan
-- =============================================================================
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
                
                -- Jika tidak ada, gunakan default 1 bulan
                IF last_freq IS NULL THEN
                    last_freq := 1;
                END IF;
                
                -- Buat jadwal baru dengan frekuensi yang ada
                INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN
                    (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                VALUES
                    (NEW.id_hewan, next_checkup_date, last_freq);
            END;
        END IF;
    END IF;
    
    -- Update status kesehatan hewan
    UPDATE HEWAN
    SET status_kesehatan = NEW.status_kesehatan
    WHERE id = NEW.id_hewan;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Buat trigger baru untuk sync medical schedule
CREATE TRIGGER trigger_sync_medical_schedule
AFTER INSERT ON CATATAN_MEDIS
FOR EACH ROW
EXECUTE FUNCTION sync_medical_record_schedule();