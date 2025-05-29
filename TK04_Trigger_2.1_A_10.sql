-- Create the corrected function
CREATE OR REPLACE FUNCTION prevent_duplicate_hewan()
RETURNS TRIGGER AS $$
DECLARE
    existing_count INTEGER;
BEGIN
    -- Check for existing records with same name, species, and origin
    SELECT COUNT(*) INTO existing_count
    FROM HEWAN
    WHERE nama = NEW.nama
      AND spesies = NEW.spesies
      AND asal_hewan = NEW.asal_hewan;

    -- If duplicate found, raise exception
    IF existing_count > 0 THEN
        RAISE EXCEPTION 'Data satwa atas nama "%", spesies "%", dan berasal dari "%" sudah terdaftar.',
            NEW.nama, NEW.spesies, NEW.asal_hewan;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER trigger_prevent_duplicate_hewan
    BEFORE INSERT ON HEWAN
    FOR EACH ROW
    EXECUTE FUNCTION prevent_duplicate_hewan();

