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
    PRIMARY KEY (id_hewan, tanggal_pemeriksaan),
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
    id_hewan UUID PRIMARY KEY,
    jadwal TIMESTAMP NOT NULL,
    username_jh VARCHAR(50),
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

-- Insert datas for 1. PENGGUNA table
-- 50 PENGUNJUNG
INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
VALUES 
('ahmad_fauzi', 'ahmad.fauzi@gmail.com', 'F4uz1Ahmad!', 'Ahmad', NULL, 'Fauzi', '081234567891'),
('bayu_setiawan', 'bayu.setiawan@yahoo.com', 'B4yuS3t1aw4n', 'Bayu', 'Adi', 'Setiawan', '081234567892'),
('citra_sakila', 'citra.lestari@gmail.com', 'C1tr454k1l4', 'Citra', NULL, 'Sakila', '081234567893'),
('dian_sastro', 'dian.sastro@hotmail.com', 'D14nS4str0!', 'Dian', NULL, 'Sastrowardoyo', '081234567894'),
('eko_patrio', 'eko.patrio@gmail.com', 'Ek0P4tr10', 'Eko', NULL, 'Patrio', '081234567895'),
('fanny_fadillah', 'fanny.fadillah@yahoo.co.id', 'F4nnyF4d1ll4h', 'Fanny', 'Nur', 'Fadillah', '081234567896'),
('galih_ginanjar', 'galih.ginanjar@gmail.com', 'G4l1hG1n4nj4r', 'Galih', NULL, 'Ginanjar', '081234567897'),
('hani_soraya', 'hani.soraya@gmail.com', 'H4n1S0r4y4', 'Hani', 'Putri', 'Soraya', '081234567898'),
('irfan_bachdim', 'irfan.bachdim@yahoo.com', '1rf4nB4chd1m', 'Irfan', NULL, 'Bachdim', '081234567899'),
('jessica_mila', 'jessica.mila@gmail.com', 'J3ss1c4M1l4', 'Jessica', 'Aurum', 'Mila', '081234567810'),
('kevin_julio', 'kevin.julio@hotmail.com', 'K3v1nJul10', 'Kevin', NULL, 'Julio', '081234567811'),
('luna_maya', 'luna.maya@gmail.com', 'Lun4M4y4!', 'Luna', NULL, 'Maya', '081234567812'),
('maudy_ayunda', 'maudy.ayunda@yahoo.co.id', 'M4udyAyund4', 'Maudy', NULL, 'Ayunda', '081234567813'),
('nicholas_saputra', 'nicholas.saputra@gmail.com', 'N1ch0l4sS4putr4', 'Nicholas', NULL, 'Saputra', '081234567814'),
('olivia_jensen', 'olivia.jensen@gmail.com', '0l1v14J3ns3n', 'Olivia', NULL, 'Jensen', '081234567815'),
('prilly_latuconsina', 'prilly.latuconsina@yahoo.com', 'Pr1llyL4tu', 'Prilly', NULL, 'Latuconsina', '081234567816'),
('quinn_avrilia', 'quinn.avrilia@gmail.com', 'Qu1nnAvr1l14', 'Quinn', 'Putri', 'Avrilia', '081234567817'),
('raisa_andriana', 'raisa.andriana@hotmail.com', 'R41s4Andr14n4', 'Raisa', NULL, 'Andriana', '081234567818'),
('surya_saputra', 'surya.saputra@gmail.com', 'Sury4S4putr4', 'Surya', 'Bima', 'Saputra', '081234567819'),
('titi_kamal', 'titi.kamal@yahoo.co.id', 'T1t1K4m4l!', 'Titi', NULL, 'Kamal', '081234567820'),
('umar_zein', 'umar.zein@gmail.com', 'Um4rZ31n', 'Umar', NULL, 'Zein', '081234567821'),
('vino_bastian', 'vino.bastian@gmail.com', 'V1n0B4st14n', 'Vino', 'Giovani', 'Bastian', '081234567822'),
('wulan_guritno', 'wulan.guritno@yahoo.com', 'Wul4nGur1tn0', 'Wulan', NULL, 'Guritno', '081234567823'),
('xavier_muhammad', 'xavier.muhammad@hotmail.com', 'X4v13rMuh4mm4d', 'Xavier', NULL, 'Muhammad', '081234567824'),
('yuki_kato', 'yuki.kato@gmail.com', 'Yuk1K4t0!', 'Yuki', NULL, 'Kato', '081234567825'),
('zaskia_adya', 'zaskia.adya@yahoo.co.id', 'Z4sk14Ady4', 'Zaskia', 'Sungkar', 'Adya', '081234567826'),
('aditya_zoni', 'aditya.zoni@gmail.com', 'Ad1ty4Z0n1', 'Aditya', NULL, 'Zoni', '081234567827'),
('bella_shofie', 'bella.shofie@gmail.com', 'B3ll4Sh0f13', 'Bella', NULL, 'Shofie', '081234567828'),
('cakra_khan', 'cakra.khan@yahoo.com', 'C4kr4Kh4n!', 'Cakra', NULL, 'Khan', '081234567829'),
('dewi_sandra', 'dewi.sandra@hotmail.com', 'D3w1S4ndr4', 'Dewi', NULL, 'Sandra', '081234567830'),
('ernest_prakasa', 'ernest.prakasa@gmail.com', '3rn3stPr4k4s4', 'Ernest', NULL, 'Prakasa', '081234567831'),
('farah_quinn', 'farah.quinn@yahoo.co.id', 'F4r4hQu1nn', 'Farah', NULL, 'Quinn', '081234567832'),
('gading_marten', 'gading.marten@gmail.com', 'G4d1ngM4rt3n', 'Gading', NULL, 'Marten', '081234567833'),
('happy_salma', 'happy.salma@gmail.com', 'H4ppyS4lm4', 'Happy', NULL, 'Salma', '081234567834'),
('indra_bekti', 'indra.bekti@yahoo.com', '1ndr4B3kt1', 'Indra', NULL, 'Bekti', '081234567835'),
('julie_estelle', 'julie.estelle@hotmail.com', 'Jul13Est3ll3', 'Julie', NULL, 'Estelle', '081234567836'),
('kimberly_ryder', 'kimberly.ryder@gmail.com', 'K1mb3rlyRyd3r', 'Kimberly', NULL, 'Ryder', '081234567837'),
('laura_basuki', 'laura.basuki@yahoo.co.id', 'L4ur4B4suk1', 'Laura', NULL, 'Basuki', '081234567838'),
('marshanda_aulia', 'marshanda.aulia@gmail.com', 'M4rsh4nd4Aul14', 'Marshanda', NULL, 'Aulia', '081234567839'),
('nikita_willy', 'nikita.willy@gmail.com', 'N1k1t4W1lly', 'Nikita', NULL, 'Willy', '081234567840'),
('olga_syahputra', 'olga.syahputra@yahoo.com', '0lg4Sy4hputr4', 'Olga', NULL, 'Syahputra', '081234567841'),
('pevita_pearce', 'pevita.pearce@hotmail.com', 'P3v1t4P34rc3', 'Pevita', NULL, 'Pearce', '081234567842'),
('qory_sandioriva', 'qory.sandioriva@gmail.com', 'Q0ryS4nd10r1v4', 'Qory', NULL, 'Sandioriva', '081234567843'),
('reza_rahadian', 'reza.rahadian@yahoo.co.id', 'R3z4R4h4d14n', 'Reza', NULL, 'Rahadian', '081234567844'),
('syahrini_zahra', 'syahrini.zahra@gmail.com', 'Sy4hr1n1Z4hr4', 'Syahrini', NULL, 'Zahra', '081234567845'),
('tara_basro', 'tara.basro@gmail.com', 'T4r4B4sr0', 'Tara', NULL, 'Basro', '081234567846'),
('uwais_qorny', 'uwais.qorny@yahoo.com', 'Uw41sQ0rny', 'Uwais', 'Al', 'Qorny', '081234567847'),
('velove_vexia', 'velove.vexia@hotmail.com', 'V3l0v3V3x14', 'Velove', NULL, 'Vexia', '081234567848'),
('widika_sidmore', 'widika.sidmore@gmail.com', 'W1d1k4S1dm0r3', 'Widika', NULL, 'Sidmore', '081234567849'),
('zacky_zimah', 'zacky.zimah@yahoo.co.id', 'Z4ckyZ1m4h', 'Zacky', NULL, 'Zimah', '081234567850');
-- 15 DOKTER_HEWAN
INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
VALUES 
('ajeng_pratiwi', 'ajeng.pratiwi@gmail.com', 'Pas$w0rd123', 'Ajeng', 'Kusuma', 'Pratiwi', '081234567890'),
('budi_santoso', 'budi.santoso@gmail.com', 'Bud1S4nt0s0!', 'Budi', 'Dharma', 'Santoso', '081298765432'),
('dewi_anggraini', 'dewi.anggraini@yahoo.com', 'D3w1Anggrn', 'Dewi', NULL, 'Anggraini', '085678901234'),
('eko_prasetyo', 'eko.prasetyo@hotmail.com', 'Ek0Pr4s3ty0', 'Eko', 'Budi', 'Prasetyo', '087812345678'),
('fitri_wulandari', 'fitri.wulandari@gmail.com', 'F1tr1Wul4n!', 'Fitri', 'Ayu', 'Wulandari', '082187654321'),
('gilang_ramadhan', 'gilang.ramadhan@yahoo.co.id', 'G1l4ngR4m4', 'Gilang', NULL, 'Ramadhan', '081345678901'),
('hendra_wijaya', 'hendra.wijaya@gmail.com', 'H3ndr4W1j4y4', 'Hendra', 'Surya', 'Wijaya', '085643219876'),
('intan_permata', 'intan.permata@gmail.com', 'Int4nP3rm4t4', 'Intan', 'Cahaya', 'Permata', '087890123456'),
('joko_susilo', 'joko.susilo@yahoo.com', 'J0k0Sus1l0', 'Joko', NULL, 'Susilo', '081456789012'),
('kartika_sari', 'kartika.sari@gmail.com', 'K4rt1k4S4r1', 'Kartika', 'Dewi', 'Sari', '082198765432'),
('luhur_prabowo', 'luhur.prabowo@hotmail.com', 'Luhur2023!', 'Luhur', 'Agung', 'Prabowo', '087654321098'),
('mawar_indah', 'mawar.indah@gmail.com', 'M4w4rInd4h', 'Mawar', NULL, 'Indah', '085612345678'),
('nugroho_santoso', 'nugroho.santoso@yahoo.co.id', 'Nugr0h0S4nt0', 'Nugroho', 'Budi', 'Santoso', '081567890123'),
('putri_maharani', 'putri.maharani@gmail.com', 'Putr1M4h4r4n1', 'Putri', 'Ayu', 'Maharani', '082109876543'),
('rizky_pratama', 'rizky.pratama@gmail.com', 'R1zkyPr4t4m4', 'Rizky', 'Aditya', 'Pratama', '087891234567');
-- 10 PENJAGA_HEWAN
INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
VALUES 
('arya_wijaya', 'arya.wijaya@gmail.com', 'Ary4W1j4y4!', 'Arya', 'Dharma', 'Wijaya', '081234567891'),
('bayu_pradana', 'bayu.pradana@gmail.com', 'B4yuPr4d4n4', 'Bayu', NULL, 'Pradana', '082345678912'),
('citra_lestari', 'citra.lestari@yahoo.com', 'C1tr4L3st4r1', 'Citra', 'Ayu', 'Lestari', '083456789123'),
('dimas_putra', 'dimas.putra@gmail.com', 'D1m4sPutr4!', 'Dimas', 'Adi', 'Putra', '084567891234'),
('elsa_safitri', 'elsa.safitri@gmail.com', 'Els4S4f1tr1', 'Elsa', NULL, 'Safitri', '085678912345'),
('fajar_ramadhan', 'fajar.ramadhan@yahoo.co.id', 'F4j4rR4m4dh4n', 'Fajar', 'Eka', 'Ramadhan', '086789123456'),
('gita_purnama', 'gita.purnama@gmail.com', 'G1t4Purn4m4', 'Gita', 'Cahaya', 'Purnama', '087891234567'),
('haris_kurniawan', 'haris.kurniawan@gmail.com', 'H4r1sKurn14w4n', 'Haris', NULL, 'Kurniawan', '088912345678'),
('indra_maulana', 'indra.maulana@yahoo.com', '1ndr4M4ul4n4', 'Indra', 'Bima', 'Maulana', '089123456789'),
('jasmine_putri', 'jasmine.putri@gmail.com', 'J4sm1n3Putr1', 'Jasmine', 'Ayu', 'Putri', '081234567890');
-- 10 PELATIH_HEWAN
INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
VALUES 
('andrea_trainer', 'andrea.trainer@hewan.com', 'Tr41n3rAndr34', 'Andrea', NULL, 'Hirata', '083234567861'),
('bagus_pelatih', 'bagus.pelatih@hewan.com', 'B4gusP3l4t1h', 'Bagus', 'Satria', 'Wirawan', '083234567862'),
('cindy_trainer', 'cindy.trainer@hewan.com', 'C1ndyTr41n3r', 'Cindy', 'Ayu', 'Larasati', '083234567863'),
('david_pelatih', 'david.pelatih@hewan.com', 'D4v1dP3l4t1h', 'David', NULL, 'Kurniawan', '083234567864'),
('elsa_trainer', 'elsa.trainer@hewan.com', '3ls4Tr41n3r', 'Elsa', 'Putri', 'Maharani', '083234567865'),
('fahmi_pelatih', 'fahmi.pelatih@hewan.com', 'F4hm1P3l4t1h', 'Fahmi', NULL, 'Alfarisi', '083234567866'),
('grace_trainer', 'grace.trainer@hewan.com', 'Gr4c3Tr41n3r', 'Grace', 'Meilani', 'Susanto', '083234567867'),
('hadi_pelatih', 'hadi.pelatih@hewan.com', 'H4d1P3l4t1h', 'Hadi', 'Gunawan', 'Wicaksono', '083234567868'),
('irene_trainer', 'irene.trainer@hewan.com', '1r3n3Tr41n3r', 'Irene', NULL, 'Setiawati', '083234567869'),
('jaya_pelatih', 'jaya.pelatih@hewan.com', 'J4y4P3l4t1h', 'Jaya', 'Putra', 'Perdana', '083234567870');
-- 10 STAF_ADMIN
INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
VALUES 
('amir_admin', 'amir.admin@hewan.com', 'Am1rAdm1n!', 'Amir', NULL, 'Mahmud', '084234567871'),
('bunga_staff', 'bunga.staff@hewan.com', 'Bung4St4ff', 'Bunga', 'Citra', 'Lestari', '084234567872'),
('candra_admin', 'candra.admin@hewan.com', 'C4ndr4Adm1n', 'Candra', 'Arif', 'Gunawan', '084234567873'),
('dina_staff', 'dina.staff@hewan.com', 'D1n4St4ff', 'Dina', NULL, 'Maulida', '084234567874'),
('eka_admin', 'eka.admin@hewan.com', '3k4Adm1n', 'Eka', 'Surya', 'Pradana', '084234567875'),
('fira_staff', 'fira.staff@hewan.com', 'F1r4St4ff', 'Fira', 'Intan', 'Puspita', '084234567876'),
('guntur_admin', 'guntur.admin@hewan.com', 'Guntur4dm1n', 'Guntur', NULL, 'Ramadhan', '084234567877'),
('hanna_staff', 'hanna.staff@hewan.com', 'H4nn4St4ff', 'Hanna', 'Nur', 'Azizah', '084234567878'),
('ivan_admin', 'ivan.admin@hewan.com', '1v4nAdm1n', 'Ivan', 'Dimas', 'Setiawan', '084234567879'),
('jasmine_staff', 'jasmine.staff@hewan.com', 'J4sm1n3St4ff', 'Jasmine', NULL, 'Anggraini', '084234567880');

-- Insert 15 datas for 3. DOKTER_HEWAN table
INSERT INTO DOKTER_HEWAN (username_DH, no_STR)
VALUES 
('ajeng_pratiwi', 'STR-DH-2021-00123456'),
('budi_santoso', 'STR-DH-2019-00234567'),
('dewi_anggraini', 'STR-DH-2020-00345678'),
('eko_prasetyo', 'STR-DH-2018-00456789'),
('fitri_wulandari', 'STR-DH-2022-00567890'),
('gilang_ramadhan', 'STR-DH-2021-00678901'),
('hendra_wijaya', 'STR-DH-2019-00789012'),
('intan_permata', 'STR-DH-2020-00890123'),
('joko_susilo', 'STR-DH-2023-00901234'),
('kartika_sari', 'STR-DH-2018-01012345'),
('luhur_prabowo', 'STR-DH-2022-01123456'),
('mawar_indah', 'STR-DH-2021-01234567'),
('nugroho_santoso', 'STR-DH-2019-01345678'),
('putri_maharani', 'STR-DH-2020-01456789'),
('rizky_pratama', 'STR-DH-2022-01567890');

-- Insert 10 datas for 4. SPESIALISASI table (jumlah dikurangi dari 17 menjadi 10)
INSERT INTO SPESIALISASI (username_SH, nama_spesialisasi)
VALUES 
('ajeng_pratiwi', 'Bedah Hewan Kecil'),
('budi_santoso', 'Kedokteran Hewan Kucing'),
('dewi_anggraini', 'Dokter Hewan Satwa Liar'),
('eko_prasetyo', 'Reproduksi Veteriner'),
('fitri_wulandari', 'Kedokteran Hewan Eksotik'),
('gilang_ramadhan', 'Radiologi Veteriner'),
('hendra_wijaya', 'Oftalmologi Hewan'),
('intan_permata', 'Onkologi Veteriner'),
('joko_susilo', 'Neurologi Hewan'),
('kartika_sari', 'Bedah Ortopedi Hewan');

-- Insert 10 datas for 4. PENJAGA_HEWAN table
INSERT INTO PENJAGA_HEWAN (username_jh, id_staf)
VALUES 
('arya_wijaya', '550e8400-e29b-41d4-a716-446655440000'),
('bayu_pradana', '550e8400-e29b-41d4-a716-446655440001'),
('citra_lestari', '550e8400-e29b-41d4-a716-446655440002'),
('dimas_putra', '550e8400-e29b-41d4-a716-446655440003'),
('elsa_safitri', '550e8400-e29b-41d4-a716-446655440004'),
('fajar_ramadhan', '550e8400-e29b-41d4-a716-446655440005'),
('gita_purnama', '550e8400-e29b-41d4-a716-446655440006'),
('haris_kurniawan', '550e8400-e29b-41d4-a716-446655440007'),
('indra_maulana', '550e8400-e29b-41d4-a716-446655440008'),
('jasmine_putri', '550e8400-e29b-41d4-a716-446655440009');

-- Insert 8 datas for 10. HABITAT table
INSERT INTO HABITAT (nama, luas_area, kapasitas, status)
VALUES 
('Hutan Hujan Tropis', 5000.75, 120, 'Aktif'),
('Padang Rumput', 3200.50, 80, 'Aktif'),
('Pegunungan', 4500.25, 60, 'Aktif'),
('Rawa', 2800.00, 45, 'Pemeliharaan'),
('Gurun', 3800.50, 30, 'Aktif'),
('Savana', 4200.75, 90, 'Aktif'),
('Terumbu Karang', 1500.25, 200, 'Aktif'),
('Hutan Bakau', 2100.50, 50, 'Renovasi');

-- Insert 40 datas into 8. HEWAN table 
INSERT INTO HEWAN (id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Raja', 'Panthera tigris sumatrae', 'Sumatera, Indonesia', '2018-03-12', 'Sehat', 'Hutan Hujan Tropis', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRdBHMhY_ICwg4ta5lg9JkF0ADznhYlJbt0JA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'Kiko', 'Pongo pygmaeus', 'Kalimantan, Indonesia', '2016-07-23', 'Sehat', 'Hutan Hujan Tropis', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTu_8lN2BoofoWQgpYfVt5XvQqPoGyiqRqvxA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'Luna', 'Elephas maximus sumatranus', 'Sumatera, Indonesia', '2014-05-17', 'Sehat', 'Hutan Hujan Tropis', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRm-beLgPGJKth2krKGtsKVyUniV5FuzevuVA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'Simba', 'Panthera leo', 'Tanzania, Afrika', '2019-01-28', 'Sehat', 'Savana', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Lion_waiting_in_Namibia.jpg/1200px-Lion_waiting_in_Namibia.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'Bolt', 'Acinonyx jubatus', 'Kenya, Afrika', '2020-04-05', 'Sehat', 'Savana', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDK5pfJ34gxt_6SVC1rgdyCChW2mriEjiLeA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a16', 'Miko', 'Hylobates moloch', 'Jawa, Indonesia', '2017-11-30', 'Sehat', 'Hutan Hujan Tropis', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT82ZTpZW85LefM57CB17cj9xc4OWGgnRlirg&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'Kiwi', 'Nasalis larvatus', 'Kalimantan, Indonesia', '2018-08-14', 'Observasi', 'Hutan Bakau', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Proboscis_monkey_%28Nasalis_larvatus%29_male_head.jpg/250px-Proboscis_monkey_%28Nasalis_larvatus%29_male_head.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a18', 'Goku', 'Macaca nigra', 'Sulawesi, Indonesia', '2019-06-22', 'Sehat', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/d/d4/Crested_Black_Macaque_%28Macaca_nigra%29.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a19', 'Rio', 'Paradisaea apoda', 'Papua, Indonesia', '2020-02-11', 'Sehat', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/c/c1/Paradisaea_apoda_-Bali_Bird_Park-5.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a20', 'Blu', 'Cacatua sulphurea', 'Nusa Tenggara, Indonesia', '2017-12-15', 'Sehat', 'Hutan Hujan Tropis', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRJmV4q0-CVbdJ85zBUB3g7A1ZAoUmPX6eMeA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21', 'Zazu', 'Buceros rhinoceros', 'Sumatera, Indonesia', '2019-04-26', 'Sehat', 'Hutan Hujan Tropis', 'https://cdn.download.ams.birds.cornell.edu/api/v2/asset/220489371/900'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'Pipi', 'Struthio camelus', 'Afrika Timur', '2018-05-05', 'Sehat', 'Savana', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRBa_RrUO3GNAs9wh72WtwusAc8-Vsbe9aUjg&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a23', 'Tiko', 'Ara ararauna', 'Brasil, Amerika Selatan', '2019-07-14', 'Sehat', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/e/ec/Ara_ararauna_Luc_Viatour.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a24', 'Kaa', 'Python reticulatus', 'Indonesia', '2017-08-29', 'Sehat', 'Hutan Hujan Tropis', 'https://cdn.britannica.com/28/239528-050-D89C8118/reticulated-python-Malayopython-reticulatus.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a25', 'Rex', 'Varanus komodoensis', 'Pulau Komodo, Indonesia', '2016-03-18', 'Sehat', 'Savana', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/202306_Varanus_komodoensis.jpg/1200px-202306_Varanus_komodoensis.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', 'Spike', 'Crocodylus porosus', 'Indonesia', '2015-01-10', 'Sakit', 'Rawa', 'https://reptile-database.reptarium.cz/content/photo_rd_02/Crocodylus-porosus-03000030135_01.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a27', 'Crush', 'Chelonia mydas', 'Indonesia', '2010-09-22', 'Sehat', 'Terumbu Karang', 'https://i0.wp.com/www.naturefiji.org/wp-content/uploads/2008/04/Green-turtle-Chelonia-mydas.jpg?ssl=1'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a28', 'Ziggy', 'Iguana iguana', 'Amerika Selatan', '2019-11-03', 'Sehat', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Iguana_iguana.jpg/1200px-Iguana_iguana.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a29', 'Dotty', 'Giraffa camelopardalis', 'Kenya, Afrika', '2017-07-21', 'Sehat', 'Savana', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1LBOAqJBIE1mB6IX7cGkwZaH7H-ksUa5hIg&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a30', 'Stripes', 'Equus quagga', 'Tanzania, Afrika', '2018-10-11', 'Sehat', 'Savana', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSJAFJ2cCC3gFAubQ8mFa77Oj8KFexvUJkM0A&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a31', 'Bruno', 'Ursus arctos', 'Kanada, Amerika Utara', '2016-05-15', 'Sehat', 'Pegunungan', 'https://upload.wikimedia.org/wikipedia/commons/7/79/2010-brown-bear.jpghttps://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVqK1DBnGuqtHFqW6P2r7aSKsHphFk049cgA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'Felix', 'Panthera onca', 'Brasil, Amerika Selatan', '2018-09-07', 'Observasi', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Jaguar_%28Panthera_onca_palustris%29_male_Three_Brothers_River_2_%28cropped%29.jpg/1200px-Jaguar_%28Panthera_onca_palustris%29_male_Three_Brothers_River_2_%28cropped%29.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a33', 'Rocky', 'Rhinoceros unicornis', 'Nepal, Asia', '2015-12-03', 'Sehat', 'Padang Rumput', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Indian_Rhino_%28Rhinoceros_unicornis%291_-_Relic38.jpg/2560px-Indian_Rhino_%28Rhinoceros_unicornis%291_-_Relic38.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a34', 'Sandy', 'Camelus dromedarius', 'Mesir, Afrika', '2016-08-25', 'Sehat', 'Gurun', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS_svbhARlCQHlXZnDRtuEKxvFwmfIDlyaBiA&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a35', 'Spiky', 'Hystrix cristata', 'Afrika Utara', '2019-03-16', 'Sehat', 'Gurun', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQzJ1uAnTuxPWpaoAPQyUQwKEOh4eGuiZ4Xw&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a36', 'Slinky', 'Uromastyx aegyptia', 'Timur Tengah', '2020-01-17', 'Sehat', 'Gurun', 'https://upload.wikimedia.org/wikipedia/commons/c/cc/Uromastyx_aegyptia_2.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a37', 'Putih', 'Tyto alba', 'Jawa, Indonesia', '2019-02-28', 'Sehat', 'Padang Rumput', 'https://www.asianagri.com/wp-content/uploads/2019/03/Asian_Agri_Tyto_Alba_-_Natural_Pest_Management_1.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a38', 'Banteng', 'Bos javanicus', 'Jawa, Indonesia', '2017-06-14', 'Sehat', 'Padang Rumput', 'https://upload.wikimedia.org/wikipedia/commons/5/5a/Banteng_Alas_Purwo.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a39', 'Badak', 'Rhinoceros sondaicus', 'Jawa, Indonesia', '2014-11-22', 'Observasi', 'Hutan Hujan Tropis', 'https://cdn-gonef.nitrocdn.com/UbWAxHlpDDRAfYTBoCBfYvGZgzkfyWTb/assets/images/optimized/rev-c08d0b4/seethewild.org/wp-content/uploads/2022/09/javan-rhinoceros-768x432-1.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a40', 'Komo', 'Babyrousa babyrussa', 'Sulawesi, Indonesia', '2018-04-19', 'Sehat', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Hirscheber1a.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a41', 'Poky', 'Echidna aculeatus', 'Australia', '2019-12-12', 'Sehat', 'Padang Rumput', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRivds8jSfrZG4d9n1wnvAB0kz2uBsrcdrTRQ&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a42', 'Hopper', 'Macropus rufus', 'Australia', '2018-07-30', 'Sehat', 'Padang Rumput', 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Red_kangaroo_-_melbourne_zoo.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a43', 'Sleepy', 'Phascolarctos cinereus', 'Australia', '2017-05-05', 'Sehat', 'Hutan Hujan Tropis', 'https://upload.wikimedia.org/wikipedia/commons/4/49/Koala_climbing_tree.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'Bubbles', 'Tursiops truncatus', 'Laut Indonesia', '2016-09-18', 'Sehat', 'Terumbu Karang', 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Tursiops_truncatus_01-cropped.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a45', 'Nemo', 'Amphiprion ocellaris', 'Laut Indonesia', '2020-03-28', 'Sehat', 'Terumbu Karang', 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Amphiprion_ocellaris_%281%29.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a46', 'Shelly', 'Eretmochelys imbricata', 'Laut Indonesia', '2015-08-07', 'Sehat', 'Terumbu Karang', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRV4VIllNN694xVvh7hFNx5X1hOHy_W78GUOg&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a47', 'Fleecy', 'Capra aegagrus hircus', 'Pegunungan Himalaya', '2019-01-03', 'Sehat', 'Pegunungan', 'https://upload.wikimedia.org/wikipedia/commons/b/b2/Hausziege_04.jpg'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a48', 'Snowy', 'Pantholops hodgsonii', 'Tibet', '2018-11-15', 'Sehat', 'Pegunungan', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS_hqUukI5jeYqWgzNRIp5U97VYSSJPW0C4JUSgUAcq4RvQc84OhCLuZhrq-PFnXYhQX-M&usqp=CAU'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a49', 'Alpine', 'Rupicapra rupicapra', 'Alpen, Eropa', '2017-10-10', 'Sehat', 'Pegunungan', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRTzBU2KN_a9XYNdmU0U9mr9Dfbyw1MLSVwSQ&s'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a50', 'Soar', 'Aquila chrysaetos', 'Amerika Utara', '2018-06-09', 'Sehat', 'Pegunungan', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgUOt1jogkXuGdvbl3UE_AiGVrJIblB3y5BA&s');

-- Insert 10 datas for 9. CATATAN_MEDIS table
INSERT INTO CATATAN_MEDIS (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ajeng_pratiwi', '2023-09-15', 'Infeksi kulit ringan', 'Antibiotik dan salep antijamur', 'Pemulihan', 'Evaluasi ulang dalam 2 minggu, pantau perkembangan luka'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'budi_santoso', '2023-10-03', 'Pemeriksaan rutin', 'Vitamin dan suplemen', 'Sehat', 'Pemeriksaan berikutnya dalam 6 bulan'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', 'dewi_anggraini', '2023-11-21', 'Infeksi saluran pernapasan', 'Antibiotik dan terapi inhalasi', 'Observasi', 'Pemantauan harian selama seminggu'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', 'eko_prasetyo', '2023-12-07', 'Infeksi pada kaki', 'Antibiotik spektrum luas dan perawatan luka', 'Sakit', 'Perawatan luka harian dan evaluasi ulang dalam 5 hari'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', 'fitri_wulandari', '2024-01-18', 'Penurunan nafsu makan', 'Stimulan nafsu makan dan vitamin', 'Observasi', 'Pantau pola makan selama 10 hari'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a39', 'gilang_ramadhan', '2024-02-05', 'Parasit internal', 'Obat cacing dan probiotik', 'Observasi', 'Pemeriksaan feses ulang dalam 2 minggu'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'hendra_wijaya', '2024-02-22', 'Masalah gigi', 'Pembersihan gigi dan pengikisan', 'Sehat', 'Pemeriksaan gigi rutin setiap 3 bulan'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'intan_permata', '2024-03-10', 'Vaksinasi rutin', 'Vaksin rabies dan distemper', 'Sehat', 'Vaksinasi berikutnya tahun depan'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', 'joko_susilo', '2024-03-25', 'Lesi kulit', 'Pengobatan antibiotik dan terapi air', 'Pemulihan', 'Evaluasi kondisi kulit setiap 3 hari'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a46', 'kartika_sari', '2024-04-12', 'Retak pada cangkang', 'Penutupan retak dengan resin khusus', 'Pemulihan', 'Pemantauan kesembuhan cangkang selama 4 minggu');

-- Insert 5 datas for 11. PAKAN table
INSERT INTO PAKAN (id_hewan, jadwal, jenis, jumlah, status)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-04-25 08:00:00', 'Daging Sapi', 8, 'Terjadwal'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2024-04-25 09:30:00', 'Buah-buahan Segar', 5, 'Selesai'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', '2024-04-25 10:15:00', 'Rumput dan Sayuran', 25, 'Selesai'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a43', '2024-04-25 13:45:00', 'Daun Eucalyptus', 3, 'Terjadwal'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', '2024-04-25 15:30:00', 'Ikan Segar', 12, 'Terjadwal');

-- Insert 5 datas for 12. MEMBERI table
INSERT INTO MEMBERI (id_hewan, jadwal, username_jh)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-04-25 08:00:00', 'arya_wijaya'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2024-04-25 09:30:00', 'bayu_pradana'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', '2024-04-25 10:15:00', 'citra_lestari'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', '2024-04-26 08:30:00', 'dimas_putra'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', '2024-04-26 09:45:00', 'elsa_safitri'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a25', '2024-04-26 11:15:00', 'fajar_ramadhan'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a43', '2024-04-26 13:45:00', 'gita_purnama'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', '2024-04-26 15:30:00', 'haris_kurniawan'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a45', '2024-04-27 10:00:00', 'indra_maulana'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a29', '2024-04-27 11:30:00', 'jasmine_putri');

-- Insert 10 datas for 17. JADWAL_PEMERIKSAAN_KESEHATAN table
INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-06-15', 3),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2024-05-03', 2),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', '2024-05-22', 1),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', '2024-06-10', 3),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a17', '2024-05-21', 1),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a26', '2024-05-05', 0.5),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32', '2024-05-18', 1),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a39', '2024-05-05', 1),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', '2024-05-25', 2),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a46', '2024-07-12', 3);

INSERT INTO FASILITAS (nama, jadwal, kapasitas_max)
VALUES 
('Zona Akuatik', '2025-05-01 09:00:00', 200),
('Amphitheater Utama', '2025-05-01 10:00:00', 300),
('Zona Harimau', '2025-05-01 11:00:00', 100),
('Area Petualangan Anak', '2025-05-01 09:30:00', 150),
('Taman Air Mini', '2025-05-01 10:30:00', 100),
('Kandang Reptil', '2025-05-01 11:30:00', 80),
('Rumah Burung', '2025-05-01 13:00:00', 120),
('Savana Afrika', '2025-05-01 14:00:00', 250),
('Hutan Hujan', '2025-05-01 15:00:00', 180),
('Taman Kupu-kupu', '2025-05-01 16:00:00', 50);

INSERT INTO ATRAKSI (nama_atraksi, lokasi)
VALUES 
('Zona Akuatik', 'Area Barat Safari'),
('Amphitheater Utama', 'Area Tengah Safari'),
('Zona Harimau', 'Area Utara Safari'),
('Area Petualangan Anak', 'Area Selatan Safari'),
('Taman Air Mini', 'Area Barat Safari');

INSERT INTO WAHANA (nama_wahana, peraturan, kapasitas, jadwal)
VALUES 
('Taman Air Mini', '1. Dilarang Berenang. 2. Dilarang membawa makanan. 3. Anak-anak harus didampingi orang dewasa.', 100, '10:00:00'),
('Area Petualangan Anak', '1. Dilarang memanjat pagar. 2. Dilarang membawa makanan dan minuman. 3. Maksimal usia 12 tahun.', 75, '11:30:00'),
('Zona Akuatik', '1. Wajib menggunakan alas kaki anti-slip. 2. Dilarang berenang. 3. Dilarang memberi makan hewan.', 150, '09:00:00'),
('Kandang Reptil', '1. Dilarang menggunakan flash kamera. 2. Dilarang mengetuk kaca. 3. Jaga jarak aman.', 80, '13:00:00'),
('Taman Kupu-kupu', '1. Jangan menyentuh kupu-kupu. 2. Dilarang membawa makanan. 3. Jaga ketenangan.', 50, '14:00:00');

INSERT INTO JADWAL_PENUGASAN (username_lh, tgl_penugasan, nama_atraksi)
VALUES 
('andrea_trainer', '2025-05-12 10:00:00', 'Zona Akuatik'),
('bagus_pelatih', '2025-05-13 11:00:00', 'Zona Harimau'),
('cindy_trainer', '2025-05-14 10:00:00', 'Amphitheater Utama'),
('david_pelatih', '2025-05-15 09:30:00', 'Area Petualangan Anak'),
('elsa_trainer', '2025-05-16 10:30:00', 'Taman Air Mini'),
('fahmi_pelatih', '2025-05-17 14:00:00', 'Zona Akuatik'),
('grace_trainer', '2025-05-18 11:00:00', 'Zona Harimau'),
('hadi_pelatih', '2025-05-19 10:00:00', 'Amphitheater Utama'),
('irene_trainer', '2025-05-20 09:30:00', 'Area Petualangan Anak'),
('jaya_pelatih', '2025-05-21 10:30:00', 'Taman Air Mini');

INSERT INTO BERPARTISIPASI (nama_fasilitas, id_hewan)
VALUES 
-- Zona Akuatik berisi lumba-lumba, penyu, ikan badut
('Zona Akuatik', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44'),  -- Bubbles (Lumba-lumba)
('Zona Akuatik', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a45'),  -- Nemo (Clownfish)
('Zona Akuatik', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a46'),  -- Shelly (Penyu)
-- Amphitheater Utama berisi burung-burung dan hewan-hewan terlatih
('Amphitheater Utama', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a19'),  -- Rio (Cendrawasih)
('Amphitheater Utama', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a20'),  -- Blu (Kakaktua)
('Amphitheater Utama', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a21'),  -- Zazu (Rangkong)
('Amphitheater Utama', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a23'),  -- Tiko (Macaw)
-- Zona Harimau berisi harimau dan kucing besar
('Zona Harimau', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),  -- Raja (Harimau Sumatera)
('Zona Harimau', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14'),  -- Simba (Singa)
('Zona Harimau', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15'),  -- Bolt (Cheetah)
('Zona Harimau', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a32'),  -- Felix (Jaguar)
-- Area Petualangan Anak berisi hewan-hewan kecil dan jinak
('Area Petualangan Anak', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a35'),  -- Spiky (Landak)
('Area Petualangan Anak', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a41'),  -- Poky (Echidna)
('Area Petualangan Anak', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a47'),  -- Fleecy (Kambing)
-- Taman Air Mini berisi kura-kura dan reptil air
('Taman Air Mini', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a27'),  -- Crush (Penyu Hijau)
('Taman Air Mini', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a26');  -- Spike (Buaya)

INSERT INTO PELATIH_HEWAN (username_lh, id_staf)
VALUES 
('andrea_trainer', '550e8400-e29b-41d4-a716-446655440010'),
('bagus_pelatih', '550e8400-e29b-41d4-a716-446655440011'),
('cindy_trainer', '550e8400-e29b-41d4-a716-446655440012'),
('david_pelatih', '550e8400-e29b-41d4-a716-446655440013'),
('elsa_trainer', '550e8400-e29b-41d4-a716-446655440014'),
('fahmi_pelatih', '550e8400-e29b-41d4-a716-446655440015'),
('grace_trainer', '550e8400-e29b-41d4-a716-446655440016'),
('hadi_pelatih', '550e8400-e29b-41d4-a716-446655440017'),
('irene_trainer', '550e8400-e29b-41d4-a716-446655440018'),
('jaya_pelatih', '550e8400-e29b-41d4-a716-446655440019');

INSERT INTO STAF_ADMIN (username_sa, id_staf) 
VALUES
('amir_admin', '770e8400-e29b-41d4-a716-667755440000'),
('bunga_staff', '770e8400-e29b-41d4-a716-667755440001'),
('candra_admin', '770e8400-e29b-41d4-a716-667755440002'),
('dina_staff', '770e8400-e29b-41d4-a716-667755440003'),
('eka_admin', '770e8400-e29b-41d4-a716-667755440004'),
('fira_staff', '770e8400-e29b-41d4-a716-667755440005'),
('guntur_admin', '770e8400-e29b-41d4-a716-667755440006'),
('hanna_staff', '770e8400-e29b-41d4-a716-667755440007'),
('ivan_admin', '770e8400-e29b-41d4-a716-667755440008'),
('jasmine_staff', '770e8400-e29b-41d4-a716-667755440009');

INSERT INTO PENGUNJUNG (username_P, alamat, tgl_lahir) 
VALUES
('ahmad_fauzi', 'Jl. Merdeka No.1, Jakarta', '1990-01-10'),
('bayu_setiawan', 'Jl. Sudirman No.2, Bandung', '1991-02-15'),
('citra_sakila', 'Jl. Diponegoro No.3, Surabaya', '1992-03-20'),
('dian_sastro', 'Jl. Thamrin No.4, Jakarta', '1993-04-25'),
('eko_patrio', 'Jl. Ahmad Yani No.5, Bogor', '1990-05-30'),
('fanny_fadillah', 'Jl. Gatot Subroto No.6, Bandung', '1991-06-05'),
('galih_ginanjar', 'Jl. Asia Afrika No.7, Surabaya', '1992-07-10'),
('hani_soraya', 'Jl. Pemuda No.8, Semarang', '1993-08-15'),
('irfan_bachdim', 'Jl. Pahlawan No.9, Yogyakarta', '1990-09-20'),
('jessica_mila', 'Jl. Gajah Mada No.10, Malang', '1991-10-25'),
('kevin_julio', 'Jl. Siliwangi No.11, Jakarta', '1992-11-30'),
('luna_maya', 'Jl. Imam Bonjol No.12, Bandung', '1993-12-05'),
('maudy_ayunda', 'Jl. Cikini No.13, Jakarta', '1990-01-10'),
('nicholas_saputra', 'Jl. Veteran No.14, Bandung', '1991-02-15'),
('olivia_jensen', 'Jl. Proklamasi No.15, Surabaya', '1992-03-20'),
('prilly_latuconsina', 'Jl. Anggrek No.16, Jakarta', '1993-04-25'),
('quinn_avrilia', 'Jl. Melati No.17, Bandung', '1990-05-30'),
('raisa_andriana', 'Jl. Kenanga No.18, Surabaya', '1991-06-05'),
('surya_saputra', 'Jl. Mawar No.19, Semarang', '1992-07-10'),
('titi_kamal', 'Jl. Teratai No.20, Yogyakarta', '1993-08-15'),
('umar_zein', 'Jl. Flamboyan No.21, Jakarta', '1990-09-20'),
('vino_bastian', 'Jl. Cempaka No.22, Bandung', '1991-10-25'),
('wulan_guritno', 'Jl. Dahlia No.23, Surabaya', '1992-11-30'),
('xavier_muhammad', 'Jl. Sakura No.24, Malang', '1993-12-05'),
('yuki_kato', 'Jl. Seruni No.25, Jakarta', '1990-01-10'),
('zaskia_adya', 'Jl. Kamboja No.26, Bandung', '1991-02-15'),
('aditya_zoni', 'Jl. Asoka No.27, Surabaya', '1992-03-20'),
('bella_shofie', 'Jl. Tanjung No.28, Jakarta', '1993-04-25'),
('cakra_khan', 'Jl. Cemara No.29, Bandung', '1990-05-30'),
('dewi_sandra', 'Jl. Cendana No.30, Surabaya', '1991-06-05'),
('ernest_prakasa', 'Jl. Sawo No.31, Semarang', '1992-07-10'),
('farah_quinn', 'Jl. Nangka No.32, Yogyakarta', '1993-08-15'),
('gading_marten', 'Jl. Duren No.33, Jakarta', '1990-09-20'),
('happy_salma', 'Jl. Mangga No.34, Bandung', '1991-10-25'),
('indra_bekti', 'Jl. Kelapa No.35, Surabaya', '1992-11-30'),
('julie_estelle', 'Jl. Alpukat No.36, Malang', '1993-12-05'),
('kimberly_ryder', 'Jl. Belimbing No.37, Jakarta', '1990-01-10'),
('laura_basuki', 'Jl. Jambu No.38, Bandung', '1991-02-15'),
('marshanda_aulia', 'Jl. Rambutan No.39, Surabaya', '1992-03-20'),
('nikita_willy', 'Jl. Pepaya No.40, Jakarta', '1993-04-25'),
('olga_syahputra', 'Jl. Pisang No.41, Bandung', '1990-05-30'),
('pevita_pearce', 'Jl. Durian No.42, Surabaya', '1991-06-05'),
('qory_sandioriva', 'Jl. Jeruk No.43, Semarang', '1992-07-10'),
('reza_rahadian', 'Jl. Apel No.44, Yogyakarta', '1993-08-15'),
('syahrini_zahra', 'Jl. Duku No.45, Jakarta', '1990-09-20'),
('tara_basro', 'Jl. Sirsak No.46, Bandung', '1991-10-25'),
('uwais_qorny', 'Jl. Kedondong No.47, Surabaya', '1992-11-30'),
('velove_vexia', 'Jl. Salak No.48, Malang', '1993-12-05'),
('widika_sidmore', 'Jl. Kersen No.49, Jakarta', '1990-01-10'),
('zacky_zimah', 'Jl. Kepel No.50, Bandung', '1991-02-15');


