-- Drop schema if exists
DROP SCHEMA IF EXISTS SIZOPI CASCADE;

-- Create schema
CREATE SCHEMA SIZOPI;

-- Set search path
SET search_path to SIZOPI;

-- 1. PENGGUNA table
CREATE TABLE PENGGUNA (
    username VARCHAR(50) PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(50) NOT NULL,
    nama_depan VARCHAR(50) NOT NULL,
    nama_tengah VARCHAR(50),
    nama_belakang VARCHAR(50) NOT NULL,
    no_telepon VARCHAR(15) NOT NULL
);

-- 2. PENGUNJUNG table
CREATE TABLE PENGUNJUNG (
    username_P VARCHAR(50) PRIMARY KEY,
    alamat VARCHAR(200) NOT NULL,
    tgl_lahir DATE NOT NULL,
    FOREIGN KEY (username_P) REFERENCES PENGGUNA(username)
);

-- 3. DOKTER_HEWAN table
CREATE TABLE DOKTER_HEWAN (
    username_DH VARCHAR(50) PRIMARY KEY,
    no_STR VARCHAR(50) NOT NULL,
    FOREIGN KEY (username_DH) REFERENCES PENGGUNA(username)
);

-- 4. SPESIALISASI table
CREATE TABLE SPESIALISASI (
    username_SH VARCHAR(50),
    nama_spesialisasi VARCHAR(100) NOT NULL,
    PRIMARY KEY (username_SH, nama_spesialisasi),
    FOREIGN KEY (username_SH) REFERENCES DOKTER_HEWAN(username_DH)
);

-- 5. PENJAGA_HEWAN table
CREATE TABLE PENJAGA_HEWAN (
    username_jh VARCHAR(50) PRIMARY KEY,
    id_staf UUID NOT NULL,
    FOREIGN KEY (username_jh) REFERENCES PENGGUNA(username)
);

-- 6. PELATIH_HEWAN table
CREATE TABLE PELATIH_HEWAN (
    username_lh VARCHAR(50) PRIMARY KEY,
    id_staf UUID NOT NULL,
    FOREIGN KEY (username_lh) REFERENCES PENGGUNA(username)
);

-- 7. STAF_ADMIN table
CREATE TABLE STAF_ADMIN (
    username_sa VARCHAR(50) PRIMARY KEY,
    id_staf UUID NOT NULL,
    FOREIGN KEY (username_sa) REFERENCES PENGGUNA(username)
);

-- 10. HABITAT table (creating this first because referenced by HEWAN)
CREATE TABLE HABITAT (
    nama VARCHAR(50) PRIMARY KEY,
    luas_area DECIMAL NOT NULL,
    kapasitas INT NOT NULL,
    status VARCHAR(100) NOT NULL
);

-- 8. HEWAN table
CREATE TABLE HEWAN (
    id UUID PRIMARY KEY,
    nama VARCHAR(100),
    spesies VARCHAR(100) NOT NULL,
    asal_hewan VARCHAR(100) NOT NULL,
    tanggal_lahir DATE,
    status_kesehatan VARCHAR(50) NOT NULL,
    nama_habitat VARCHAR(100),
    url_foto VARCHAR(255) NOT NULL,
    FOREIGN KEY (nama_habitat) REFERENCES HABITAT(nama)
);

-- 9. CATATAN_MEDIS table
CREATE TABLE CATATAN_MEDIS (
    id_hewan UUID,
    username_dh VARCHAR(50),
    tanggal_pemeriksaan DATE,
    diagnosis VARCHAR(100),
    pengobatan VARCHAR(100),
    status_kesehatan VARCHAR(50) NOT NULL,
    catatan_tindak_lanjut VARCHAR(100),
    PRIMARY KEY (id_hewan, username_dh, tanggal_pemeriksaan),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id),
    FOREIGN KEY (username_dh) REFERENCES DOKTER_HEWAN(username_DH)
);

-- 11. PAKAN table
CREATE TABLE PAKAN (
    id_hewan UUID,
    jadwal TIMESTAMP,
    jenis VARCHAR(50) NOT NULL,
    jumlah INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_hewan, jadwal),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
);

-- 12. MEMBERI table
CREATE TABLE MEMBERI (
    id_hewan UUID,
    jadwal TIMESTAMP NOT NULL,
    username_jh VARCHAR(50),
    PRIMARY KEY (id_hewan, username_jh),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id),
    FOREIGN KEY (username_jh) REFERENCES PENJAGA_HEWAN(username_jh)
);

-- 13. FASILITAS table
CREATE TABLE FASILITAS (
    nama VARCHAR(50) PRIMARY KEY,
    jadwal TIMESTAMP NOT NULL,
    kapasitas_max INT NOT NULL
);

-- 14. ATRAKSI table
CREATE TABLE ATRAKSI (
    nama_atraksi VARCHAR(50) PRIMARY KEY,
    lokasi VARCHAR(100) NOT NULL,
    FOREIGN KEY (nama_atraksi) REFERENCES FASILITAS(nama)
);

-- 15. JADWAL_PENUGASAN table
CREATE TABLE JADWAL_PENUGASAN (
    username_lh VARCHAR(50),
    tgl_penugasan TIMESTAMP,
    nama_atraksi VARCHAR(50),
    PRIMARY KEY (username_lh, tgl_penugasan),
    FOREIGN KEY (username_lh) REFERENCES PELATIH_HEWAN(username_lh),
    FOREIGN KEY (nama_atraksi) REFERENCES ATRAKSI(nama_atraksi)
);

-- 16. BERPARTISIPASI table
CREATE TABLE BERPARTISIPASI (
    nama_fasilitas VARCHAR(50),
    id_hewan UUID,
    PRIMARY KEY (nama_fasilitas, id_hewan),
    FOREIGN KEY (nama_fasilitas) REFERENCES FASILITAS(nama),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
);

-- 17. JADWAL_PEMERIKSAAN_KESEHATAN table
CREATE TABLE JADWAL_PEMERIKSAAN_KESEHATAN (
    id_hewan UUID,
    tgl_pemeriksaan_selanjutnya DATE,
    freq_pemeriksaan_rutin INT NOT NULL,
    PRIMARY KEY (id_hewan, tgl_pemeriksaan_selanjutnya),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
);

-- 18. WAHANA table
CREATE TABLE WAHANA (
    nama_wahana VARCHAR(50) PRIMARY KEY,
    peraturan TEXT NOT NULL,
    FOREIGN KEY (nama_wahana) REFERENCES FASILITAS(nama)
);

-- 19. ADOPTER table
CREATE TABLE ADOPTER (
    username_adopter VARCHAR(50) UNIQUE,
    id_adopter UUID PRIMARY KEY,
    total_kontribusi INT NOT NULL,
    FOREIGN KEY (username_adopter) REFERENCES PENGUNJUNG(username_P)
);

-- 20. INDIVIDU table
CREATE TABLE INDIVIDU (
    nik CHAR(16) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    id_adopter UUID,
    FOREIGN KEY (id_adopter) REFERENCES ADOPTER(id_adopter)
);

-- 21. ORGANISASI table
CREATE TABLE ORGANISASI (
    npp CHAR(8) PRIMARY KEY,
    nama_organisasi VARCHAR(100) NOT NULL,
    id_adopter UUID,
    FOREIGN KEY (id_adopter) REFERENCES ADOPTER(id_adopter)
);

-- 22. ADOPSI table
CREATE TABLE ADOPSI (
    id_adopter UUID,
    id_hewan UUID,
    status_pembayaran VARCHAR(10) NOT NULL,
    tgl_mulai_adopsi DATE,
    tgl_berhenti_adopsi DATE NOT NULL,
    kontribusi_finansial INT NOT NULL,
    PRIMARY KEY (id_adopter, id_hewan, tgl_mulai_adopsi),
    FOREIGN KEY (id_adopter) REFERENCES ADOPTER(id_adopter),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
);