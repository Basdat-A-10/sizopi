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