CREATE OR REPLACE FUNCTION log_riwayat_perubahan()
RETURNS TRIGGER AS $$
BEGIN

    INSERT INTO RIWAYAT_SATWA (
        id_hewan,
        old_status_kesehatan,
        new_status_kesehatan,
        old_nama_habitat,
        new_nama_habitat
    )
    VALUES (
        NEW.id,
        OLD.status_kesehatan,
        NEW.status_kesehatan,
        OLD.nama_habitat,
        NEW.nama_habitat
    );

    RAISE NOTICE 'SUKSES: Riwayat perubahan status kesehatan dari “%” menjadi “%” atau habitat dari “%” menjadi “%” telah dicatat.',
        OLD.status_kesehatan, NEW.status_kesehatan, OLD.nama_habitat, NEW.nama_habitat;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_riwayat_perubahan
AFTER UPDATE OF status_kesehatan, nama_habitat ON HEWAN
FOR EACH ROW
EXECUTE FUNCTION log_riwayat_perubahan();