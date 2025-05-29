DROP TRIGGER IF EXISTS trigger_check_kapasitas_reservasi ON RESERVASI;

CREATE OR REPLACE FUNCTION check_kapasitas_reservasi()
RETURNS TRIGGER AS $$
DECLARE
    kapasitas_max INTEGER;
    total_reserved INTEGER;
    sisa_kapasitas INTEGER;
    facility_type TEXT;
BEGIN
    SELECT F.kapasitas_max 
    INTO kapasitas_max
    FROM FASILITAS F
    WHERE F.nama = NEW.nama_fasilitas;

    IF kapasitas_max IS NULL THEN
        RAISE EXCEPTION 'ERROR: Fasilitas "%" tidak ditemukan.', NEW.nama_fasilitas;
    END IF;

    SELECT COALESCE(SUM(jumlah_tiket), 0) 
    INTO total_reserved
    FROM RESERVASI
    WHERE nama_fasilitas = NEW.nama_fasilitas
      AND tanggal_kunjungan = NEW.tanggal_kunjungan
      AND status != 'Cancelled'
      AND NOT (username_p = NEW.username_p AND nama_fasilitas = NEW.nama_fasilitas AND tanggal_kunjungan = NEW.tanggal_kunjungan);

    sisa_kapasitas := kapasitas_max - total_reserved;

    IF EXISTS (SELECT 1 FROM WAHANA WHERE nama_wahana = NEW.nama_fasilitas) THEN
        facility_type := 'wahana';
    ELSE
        facility_type := 'fasilitas';
    END IF;

    IF NEW.jumlah_tiket > sisa_kapasitas THEN
        RAISE EXCEPTION 'ERROR: Kapasitas tersisa "%" tiket, % tidak mencukupi untuk sejumlah "%" tiket yang diminta.', 
            sisa_kapasitas, facility_type, NEW.jumlah_tiket;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_kapasitas_reservasi BEFORE INSERT OR UPDATE ON RESERVASI FOR EACH ROW EXECUTE FUNCTION check_kapasitas_reservasi();

CREATE OR REPLACE FUNCTION buat_reservasi_dengan_check(
    p_username VARCHAR,
    p_nama_fasilitas VARCHAR,
    p_tanggal_kunjungan DATE,
    p_jumlah_tiket INTEGER
)
RETURNS TEXT AS $$
DECLARE
    kapasitas_max INTEGER;
    total_reserved INTEGER;
    sisa_kapasitas INTEGER;
    facility_type TEXT;
BEGIN
    SELECT F.kapasitas_max 
    INTO kapasitas_max
    FROM FASILITAS F
    WHERE F.nama = p_nama_fasilitas;

    IF kapasitas_max IS NULL THEN
        RETURN 'ERROR: Fasilitas "' || p_nama_fasilitas || '" tidak ditemukan.';
    END IF;

    SELECT COALESCE(SUM(jumlah_tiket), 0) 
    INTO total_reserved
    FROM RESERVASI
    WHERE nama_fasilitas = p_nama_fasilitas
      AND tanggal_kunjungan = p_tanggal_kunjungan
      AND status != 'Cancelled';

    sisa_kapasitas := kapasitas_max - total_reserved;

    SELECT CASE 
        WHEN EXISTS (SELECT 1 FROM WAHANA WHERE nama_wahana = p_nama_fasilitas) 
        THEN 'wahana'
        ELSE 'atraksi'
    END INTO facility_type;

    IF p_jumlah_tiket > sisa_kapasitas THEN
        RETURN 'ERROR: Kapasitas tersisa "' || sisa_kapasitas || '" tiket, ' || facility_type || ' tidak mencukupi untuk sejumlah "' || p_jumlah_tiket || '" tiket yang diminta.';
    END IF;

    INSERT INTO RESERVASI (username_p, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status)
    VALUES (p_username, p_nama_fasilitas, p_tanggal_kunjungan, p_jumlah_tiket, 'Pending');

    RETURN 'SUKSES: Reservasi berhasil dibuat untuk ' || facility_type || ' "' || p_nama_fasilitas || '" pada tanggal ' || p_tanggal_kunjungan || ' dengan ' || p_jumlah_tiket || ' tiket.';

EXCEPTION
    WHEN OTHERS THEN
        RETURN 'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;