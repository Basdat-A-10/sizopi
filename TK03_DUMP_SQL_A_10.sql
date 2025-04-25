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
    jadwal DATETIME,
    jenis VARCHAR(50) NOT NULL,
    jumlah INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_hewan, jadwal),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
);

-- 12. MEMBERI table
CREATE TABLE MEMBERI (
    id_hewan UUID PRIMARY KEY,
    jadwal DATETIME NOT NULL,
    username_jh VARCHAR(50),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id),
    FOREIGN KEY (username_jh) REFERENCES PENJAGA_HEWAN(username_jh)
);

-- 13. FASILITAS table
CREATE TABLE FASILITAS (
    nama VARCHAR(50) PRIMARY KEY,
    jadwal DATETIME NOT NULL,
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
    tgl_penugasan DATETIME,
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

-- Insert datas for 1. PENGGUNA table, 15 DOKTER_HEWAN
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

-- Insert datas for 1. PENGGUNA table, 10 PENJAGA_HEWAN
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

-- Insert 10 datas for 4. SPESIALISASI table
INSERT INTO SPESIALISASI (username_SH, nama_spesialisasi)
VALUES 
('ajeng_pratiwi', 'Bedah Hewan Kecil'),
('ajeng_pratiwi', 'Dermatologi Veteriner'),
('budi_santoso', 'Kedokteran Hewan Kucing'),
('dewi_anggraini', 'Dokter Hewan Satwa Liar'),
('dewi_anggraini', 'Konservasi Satwa Langka'),
('eko_prasetyo', 'Reproduksi Veteriner'),
('fitri_wulandari', 'Kedokteran Hewan Eksotik'),
('gilang_ramadhan', 'Radiologi Veteriner'),
('hendra_wijaya', 'Oftalmologi Hewan'),
('intan_permata', 'Onkologi Veteriner'),
('joko_susilo', 'Neurologi Hewan'),
('kartika_sari', 'Bedah Ortopedi Hewan'),
('luhur_prabowo', 'Kedokteran Hewan Reptil'),
('mawar_indah', 'Kardiologi Veteriner'),
('nugroho_santoso', 'Kedokteran Hewan Unggas'),
('putri_maharani', 'Nutrisi Hewan'),
('rizky_pratama', 'Parasitologi Veteriner');

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

-- Insert 5 datas for 11. PAKAN table
INSERT INTO PAKAN (id_hewan, jadwal, jenis, jumlah, status)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2024-04-25 08:00:00', 'Daging Sapi', 8, 'Terjadwal'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', '2024-04-25 09:30:00', 'Buah-buahan Segar', 5, 'Selesai'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', '2024-04-25 10:15:00', 'Rumput dan Sayuran', 25, 'Selesai'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a43', '2024-04-25 13:45:00', 'Daun Eucalyptus', 3, 'Terjadwal'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a44', '2024-04-25 15:30:00', 'Ikan Segar', 12, 'Terjadwal');

-- Insert 10 datas for 12. MEMBERI table
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