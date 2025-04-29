from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse, Http404
from django.contrib import messages

# View utama - menampilkan daftar wahana dan atraksi
def daftar_wahana_dan_atraksi(request):
    # Ambil username dari cookie
    username = request.COOKIES.get('user_id')
    
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")  

        # Wahana
        cursor.execute("""
            SELECT
                W.nama_wahana,
                F.kapasitas_max,
                F.jadwal,
                W.peraturan
            FROM
                WAHANA W
            JOIN
                FASILITAS F ON W.nama_wahana = F.nama
            ORDER BY
                W.nama_wahana
        """)
        wahana_columns = [col[0] for col in cursor.description]
        wahana_rows = cursor.fetchall()
        wahana_list = [dict(zip(wahana_columns, row)) for row in wahana_rows]

        # Atraksi
        cursor.execute("""
            SELECT 
                A.nama_atraksi,
                F.kapasitas_max,
                A.lokasi,
                F.jadwal,
                STRING_AGG(DISTINCT H.nama, ', ') AS hewan_terlibat,
                STRING_AGG(
                    DISTINCT 
                    TRIM(
                        CONCAT(
                            P.nama_depan, ' ',
                            COALESCE(P.nama_tengah || ' ', ''),
                            P.nama_belakang
                        )
                    ), 
                ', ') AS pelatih
            FROM 
                ATRAKSI A
            JOIN 
                FASILITAS F ON A.nama_atraksi = F.nama
            LEFT JOIN 
                BERPARTISIPASI B ON F.nama = B.nama_fasilitas
            LEFT JOIN 
                HEWAN H ON B.id_hewan = H.id
            LEFT JOIN 
                JADWAL_PENUGASAN JP ON A.nama_atraksi = JP.nama_atraksi
            LEFT JOIN 
                PELATIH_HEWAN PH ON JP.username_lh = PH.username_lh
            LEFT JOIN 
                PENGGUNA P ON PH.username_lh = P.username
            GROUP BY 
                A.nama_atraksi, F.kapasitas_max, A.lokasi, F.jadwal
            ORDER BY 
                A.nama_atraksi
        """)
        atraksi_columns = [col[0] for col in cursor.description]
        atraksi_rows = cursor.fetchall()
        atraksi_list = [dict(zip(atraksi_columns, row)) for row in atraksi_rows]
        
        # Reservasi (jika user sudah login)
        reservasi_list = []
        if username:
            cursor.execute("""
                SELECT
                    r.username_p,
                    r.nama_atraksi,
                    a.lokasi,
                    f.jadwal,
                    r.tanggal_kunjungan,
                    r.jumlah_tiket,
                    r.status
                FROM
                    RESERVASI r
                JOIN
                    ATRAKSI a ON r.nama_atraksi = a.nama_atraksi
                JOIN
                    FASILITAS f ON a.nama_atraksi = f.nama
                WHERE
                    r.username_p = %s
                ORDER BY
                    r.tanggal_kunjungan DESC
            """, [username])
            
            reservasi_columns = [col[0] for col in cursor.description]
            reservasi_rows = cursor.fetchall()
            reservasi_list = [dict(zip(reservasi_columns, row)) for row in reservasi_rows]

    return render(request, 'wahana_atraksi/daftar_wahana_dan_atraksi.html', {
        'wahana_list': wahana_list,
        'atraksi_list': atraksi_list,
        'reservasi_list': reservasi_list,
        'is_logged_in': bool(username)
    })

# Tambah Wahana dengan pengecekan duplikasi
def tambah_wahana(request):
    if request.method == "POST":
        nama_wahana = request.POST['nama_wahana']
        kapasitas_max = request.POST['kapasitas_max']
        jadwal_time = request.POST['jadwal']
        
        # Konversi format jadwal ke timestamp
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        jadwal_timestamp = f"{today} {jadwal_time}:00"
        
        peraturan = request.POST.getlist('peraturan[]')
        peraturan_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(peraturan) if p])
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Periksa apakah nama wahana sudah ada
            cursor.execute("""
                SELECT nama FROM FASILITAS WHERE nama = %s
            """, [nama_wahana])
            
            if cursor.fetchone():
                # Jika nama sudah ada, tampilkan form lagi dengan pesan error
                return render(request, 'wahana_atraksi/tambah_wahana.html', {
                    'error_message': f"Wahana atau fasilitas dengan nama '{nama_wahana}' sudah ada. Silahkan gunakan nama yang berbeda.",
                    'form_data': {
                        'nama_wahana': nama_wahana,
                        'kapasitas_max': kapasitas_max,
                        'jadwal': jadwal_time,
                        'peraturan_list': peraturan
                    }
                })
            
            # Jika nama belum ada, lanjutkan proses insert
            # Insert ke tabel FASILITAS
            cursor.execute("""
                INSERT INTO FASILITAS
                    (nama, kapasitas_max, jadwal)
                VALUES (%s, %s, %s)
            """, [nama_wahana, kapasitas_max, jadwal_timestamp])
            
            # Insert ke tabel WAHANA
            cursor.execute("""
                INSERT INTO WAHANA
                    (nama_wahana, peraturan)
                VALUES (%s, %s)
            """, [nama_wahana, peraturan_str])
            
        return redirect('daftar_wahana_dan_atraksi')
        
    return render(request, 'wahana_atraksi/tambah_wahana.html')

# Edit Wahana
# Edit Wahana - perbaikan cursor already closed
def edit_wahana(request, nama_wahana):
    if request.method == 'POST':
        kapasitas_max = request.POST.get('kapasitas_max')
        jadwal_time = request.POST.get('jadwal')
        
        # Konversi format jadwal ke timestamp
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        jadwal_timestamp = f"{today} {jadwal_time}:00"
        
        peraturan = request.POST.getlist('peraturan[]')
        peraturan_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(peraturan) if p])

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            cursor.execute("""
                UPDATE FASILITAS SET kapasitas_max = %s, jadwal = %s WHERE nama = %s
            """, [kapasitas_max, jadwal_timestamp, nama_wahana])

            cursor.execute("""
                UPDATE WAHANA SET peraturan = %s WHERE nama_wahana = %s
            """, [peraturan_str, nama_wahana])

        return redirect('daftar_wahana_dan_atraksi')
    else:
        # Data wahana
        wahana = {}
        
        # Gunakan satu blok with untuk semua operasi database
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            cursor.execute("""
                SELECT
                    W.nama_wahana,
                    F.kapasitas_max,
                    F.jadwal,
                    W.peraturan
                FROM
                    WAHANA W
                JOIN
                    FASILITAS F ON W.nama_wahana = F.nama
                WHERE
                    W.nama_wahana = %s
            """, [nama_wahana])
            row = cursor.fetchone()
            
            if not row:
                raise Http404("Wahana tidak ditemukan")
            
            # Ekstrak time dari timestamp jika perlu
            import datetime
            jadwal = row[2]
            if isinstance(jadwal, datetime.datetime):
                jadwal_time = jadwal.strftime('%H:%M')
            else:
                # Jika jadwal sudah dalam bentuk string, coba ekstrak waktu
                try:
                    from datetime import datetime
                    parsed_datetime = datetime.strptime(str(jadwal), '%Y-%m-%d %H:%M:%S')
                    jadwal_time = parsed_datetime.strftime('%H:%M')
                except:
                    jadwal_time = str(jadwal)
                
            wahana = {
                'nama_wahana': row[0],
                'kapasitas_max': row[1],
                'jadwal': jadwal_time,
                'peraturan': row[3],
                'peraturan_list': []  # Inisialisasi dengan list kosong
            }
            
            # Parse peraturan menjadi list
            if wahana['peraturan']:
                for line in wahana['peraturan'].split('\n'):
                    # Hapus nomor dan titik di awal
                    if '.' in line:
                        wahana['peraturan_list'].append(line.split('.', 1)[1].strip())
                    else:
                        wahana['peraturan_list'].append(line.strip())
        
        # Render template dengan data wahana
        return render(request, 'wahana_atraksi/edit_wahana.html', {
            'wahana': wahana
        })

# Delete Wahana
# Delete Wahana - perbaikan urutan penghapusan untuk mengatasi foreign key constraint
def delete_wahana(request, nama_wahana):
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # 1. Hapus data dari WAHANA terlebih dahulu
        cursor.execute("""
            DELETE FROM WAHANA WHERE nama_wahana = %s
        """, [nama_wahana])
        
        # 2. Terakhir, hapus data dari FASILITAS
        cursor.execute("""
            DELETE FROM FASILITAS WHERE nama = %s
        """, [nama_wahana])
        
    return redirect('daftar_wahana_dan_atraksi')

# Tambah Atraksi dengan pengecekan duplikasi
def tambah_atraksi(request):
    if request.method == "POST":
        nama_atraksi = request.POST['nama_atraksi']
        lokasi = request.POST['lokasi']
        kapasitas_max = request.POST['kapasitas_max']
        jadwal_time = request.POST['jadwal']
        
        # Konversi format jadwal ke timestamp
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        jadwal_timestamp = f"{today} {jadwal_time}:00"
        
        pelatih = request.POST.get('pelatih', '')
        hewan_terlibat = request.POST.getlist('hewan[]')
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Periksa apakah nama atraksi sudah ada
            cursor.execute("""
                SELECT nama FROM FASILITAS WHERE nama = %s
            """, [nama_atraksi])
            
            if cursor.fetchone():
                # Jika nama sudah ada, tampilkan form lagi dengan pesan error
                with connection.cursor() as cursor2:
                    cursor2.execute("SET search_path TO SIZOPI;")
                    # Ambil pelatih
                    cursor2.execute("""
                        SELECT
                            PH.username_lh,
                            TRIM(CONCAT(P.nama_depan, ' ', COALESCE(P.nama_tengah || ' ', ''), P.nama_belakang)) AS nama_lengkap
                        FROM
                            PELATIH_HEWAN PH
                        JOIN
                            PENGGUNA P ON PH.username_lh = P.username
                        ORDER BY
                            nama_lengkap
                    """)
                    pelatih_list = [{'username': row[0], 'nama': row[1]} for row in cursor2.fetchall()]
                    
                    # Ambil hewan
                    cursor2.execute("""
                        SELECT
                            id, nama, spesies
                        FROM
                            HEWAN
                        ORDER BY
                            nama
                    """)
                    hewan_list = [{'id': row[0], 'nama': row[1], 'jenis': row[2]} for row in cursor2.fetchall()]
                
                return render(request, 'wahana_atraksi/tambah_atraksi.html', {
                    'pelatih_list': pelatih_list,
                    'hewan_list': hewan_list,
                    'error_message': f"Atraksi atau fasilitas dengan nama '{nama_atraksi}' sudah ada. Silahkan gunakan nama yang berbeda.",
                    'form_data': {
                        'nama_atraksi': nama_atraksi,
                        'lokasi': lokasi,
                        'kapasitas_max': kapasitas_max,
                        'jadwal': jadwal_time,
                        'pelatih': pelatih,
                        'hewan_ids': hewan_terlibat
                    }
                })
            
            # Jika nama belum ada, lanjutkan proses insert
            # Insert ke tabel FASILITAS
            cursor.execute("""
                INSERT INTO FASILITAS
                    (nama, kapasitas_max, jadwal)
                VALUES (%s, %s, %s)
            """, [nama_atraksi, kapasitas_max, jadwal_timestamp])
            
            # Insert ke tabel ATRAKSI
            cursor.execute("""
                INSERT INTO ATRAKSI
                    (nama_atraksi, lokasi)
                VALUES (%s, %s)
            """, [nama_atraksi, lokasi])
            
            # Insert ke tabel JADWAL_PENUGASAN jika ada pelatih
            if pelatih:
                cursor.execute("""
                    INSERT INTO JADWAL_PENUGASAN
                        (username_lh, nama_atraksi, tgl_penugasan)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, [pelatih, nama_atraksi])
            
            # Insert ke tabel BERPARTISIPASI untuk hewan-hewan yang terlibat
            for hewan_id in hewan_terlibat:
                cursor.execute("""
                    INSERT INTO BERPARTISIPASI
                        (id_hewan, nama_fasilitas)
                    VALUES (%s, %s)
                """, [hewan_id, nama_atraksi])
            
        return redirect('daftar_wahana_dan_atraksi')
    
    # Ambil daftar pelatih dan hewan untuk dropdown
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        # Ambil pelatih
        cursor.execute("""
            SELECT
                PH.username_lh,
                TRIM(CONCAT(P.nama_depan, ' ', COALESCE(P.nama_tengah || ' ', ''), P.nama_belakang)) AS nama_lengkap
            FROM
                PELATIH_HEWAN PH
            JOIN
                PENGGUNA P ON PH.username_lh = P.username
            ORDER BY
                nama_lengkap
        """)
        pelatih_list = [{'username': row[0], 'nama': row[1]} for row in cursor.fetchall()]
        
        # Ambil hewan - menggunakan spesies daripada jenis
        cursor.execute("""
            SELECT
                id, nama, spesies
            FROM
                HEWAN
            ORDER BY
                nama
        """)
        hewan_list = [{'id': row[0], 'nama': row[1], 'jenis': row[2]} for row in cursor.fetchall()]
    
    return render(request, 'wahana_atraksi/tambah_atraksi.html', {
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list
    })

# Edit Atraksi
# Edit Atraksi - perbaikan cursor already closed
def edit_atraksi(request, nama_atraksi):
    if request.method == 'POST':
        kapasitas_max = request.POST.get('kapasitas_max')
        lokasi = request.POST.get('lokasi')
        jadwal_time = request.POST.get('jadwal')
        
        # Konversi format jadwal ke timestamp
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        jadwal_timestamp = f"{today} {jadwal_time}:00"
        
        pelatih = request.POST.get('pelatih', '')
        hewan_terlibat = request.POST.getlist('hewan[]')

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            # Update FASILITAS
            cursor.execute("""
                UPDATE FASILITAS SET kapasitas_max = %s, jadwal = %s WHERE nama = %s
            """, [kapasitas_max, jadwal_timestamp, nama_atraksi])

            # Update ATRAKSI
            cursor.execute("""
                UPDATE ATRAKSI SET lokasi = %s WHERE nama_atraksi = %s
            """, [lokasi, nama_atraksi])
            
            # Update pelatih - gunakan nama kolom yang benar (tgl_penugasan)
            cursor.execute("""
                DELETE FROM JADWAL_PENUGASAN WHERE nama_atraksi = %s
            """, [nama_atraksi])
            
            if pelatih:
                cursor.execute("""
                    INSERT INTO JADWAL_PENUGASAN
                        (username_lh, nama_atraksi, tgl_penugasan)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, [pelatih, nama_atraksi])
            
            # Update hewan yang terlibat
            cursor.execute("""
                DELETE FROM BERPARTISIPASI WHERE nama_fasilitas = %s
            """, [nama_atraksi])
            
            for hewan_id in hewan_terlibat:
                cursor.execute("""
                    INSERT INTO BERPARTISIPASI
                        (id_hewan, nama_fasilitas)
                    VALUES (%s, %s)
                """, [hewan_id, nama_atraksi])

        return redirect('daftar_wahana_dan_atraksi')
    else:
        # Data atraksi
        atraksi = {}
        # Daftar pelatih dan hewan
        pelatih_list = []
        hewan_list = []
        
        # Gunakan satu blok with untuk semua operasi database
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Ambil data atraksi yang akan diedit
            cursor.execute("""
                SELECT
                    A.nama_atraksi,
                    F.kapasitas_max,
                    A.lokasi,
                    F.jadwal
                FROM
                    ATRAKSI A
                JOIN
                    FASILITAS F ON A.nama_atraksi = F.nama
                WHERE
                    A.nama_atraksi = %s
            """, [nama_atraksi])
            row = cursor.fetchone()
            
            if not row:
                raise Http404("Atraksi tidak ditemukan")
                
            # Ekstrak time dari timestamp jika perlu
            import datetime
            jadwal = row[3]
            if isinstance(jadwal, datetime.datetime):
                jadwal_time = jadwal.strftime('%H:%M')
            else:
                # Jika jadwal sudah dalam bentuk string, coba ekstrak waktu
                try:
                    from datetime import datetime
                    parsed_datetime = datetime.strptime(str(jadwal), '%Y-%m-%d %H:%M:%S')
                    jadwal_time = parsed_datetime.strftime('%H:%M')
                except:
                    jadwal_time = str(jadwal)
                
            atraksi = {
                'nama_atraksi': row[0],
                'kapasitas_max': row[1],
                'lokasi': row[2],
                'jadwal': jadwal_time,
                'hewan_ids': []  # Inisialisasi dengan list kosong
            }
            
            # Ambil pelatih untuk atraksi ini
            cursor.execute("""
                SELECT
                    JP.username_lh
                FROM
                    JADWAL_PENUGASAN JP
                WHERE
                    JP.nama_atraksi = %s
                LIMIT 1
            """, [nama_atraksi])
            pelatih_row = cursor.fetchone()
            atraksi['pelatih'] = pelatih_row[0] if pelatih_row else ''
            
            # Ambil hewan yang terlibat dalam atraksi ini
            cursor.execute("""
                SELECT
                    H.id
                FROM
                    BERPARTISIPASI B
                JOIN
                    HEWAN H ON B.id_hewan = H.id
                WHERE
                    B.nama_fasilitas = %s
            """, [nama_atraksi])
            atraksi['hewan_ids'] = [row[0] for row in cursor.fetchall()]
            
            # Ambil daftar pelatih untuk dropdown
            cursor.execute("""
                SELECT
                    PH.username_lh,
                    TRIM(CONCAT(P.nama_depan, ' ', COALESCE(P.nama_tengah || ' ', ''), P.nama_belakang)) AS nama_lengkap
                FROM
                    PELATIH_HEWAN PH
                JOIN
                    PENGGUNA P ON PH.username_lh = P.username
                ORDER BY
                    nama_lengkap
            """)
            pelatih_list = [{'username': row[0], 'nama': row[1]} for row in cursor.fetchall()]
            
            # Ambil hewan untuk dropdown
            cursor.execute("""
                SELECT
                    id, nama, spesies
                FROM
                    HEWAN
                ORDER BY
                    nama
            """)
            hewan_list = [{'id': row[0], 'nama': row[1], 'jenis': row[2]} for row in cursor.fetchall()]
        
        # Render template dengan semua data yang sudah diambil
        return render(request, 'wahana_atraksi/edit_atraksi.html', {
            'atraksi': atraksi,
            'pelatih_list': pelatih_list,
            'hewan_list': hewan_list
        })

# Delete Atraksi
# Delete Atraksi - perbaikan urutan penghapusan untuk mengatasi foreign key constraint
def delete_atraksi(request, nama_atraksi):
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # 1. Hapus data dari BERPARTISIPASI terlebih dahulu
        cursor.execute("""
            DELETE FROM BERPARTISIPASI WHERE nama_fasilitas = %s
        """, [nama_atraksi])
        
        # 2. Hapus data dari JADWAL_PENUGASAN
        cursor.execute("""
            DELETE FROM JADWAL_PENUGASAN WHERE nama_atraksi = %s
        """, [nama_atraksi])
        
        # 3. Hapus data dari ATRAKSI
        cursor.execute("""
            DELETE FROM ATRAKSI WHERE nama_atraksi = %s
        """, [nama_atraksi])
        
        # 4. Terakhir, hapus data dari FASILITAS
        cursor.execute("""
            DELETE FROM FASILITAS WHERE nama = %s
        """, [nama_atraksi])
        
    return redirect('daftar_wahana_dan_atraksi')

# View untuk menampilkan form reservasi
def tampil_form_reservasi(request, nama_atraksi):
    # Ambil username dari cookie
    username = request.COOKIES.get('user_id')
    
    if not username:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    # Ambil data atraksi
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil detail atraksi
        cursor.execute("""
            SELECT
                A.nama_atraksi,
                F.kapasitas_max,
                A.lokasi,
                F.jadwal
            FROM
                ATRAKSI A
            JOIN
                FASILITAS F ON A.nama_atraksi = F.nama
            WHERE
                A.nama_atraksi = %s
        """, [nama_atraksi])
        
        atraksi = cursor.fetchone()
        
        if not atraksi:
            raise Http404("Atraksi tidak ditemukan")
        
        atraksi_data = {
            'nama_atraksi': atraksi[0],
            'kapasitas_max': atraksi[1],
            'lokasi': atraksi[2],
            'jadwal': atraksi[3]
        }
    
    # Tambahkan tanggal hari ini untuk set min date input
    from datetime import date
    today = date.today()
    
    return render(request, 'wahana_atraksi/tambah_reservasi.html', {
        'atraksi': atraksi_data,
        'today': today
    })

# View untuk membuat reservasi baru
def buat_reservasi(request):
    # Ambil username dari cookie
    username = request.COOKIES.get('user_id')
    
    if not username:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    if request.method == "POST":
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
        jumlah_tiket = request.POST.get('jumlah_tiket')
        
        # Default status saat reservasi dibuat
        status = "Pending"
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Cek apakah atraksi tersedia pada tanggal dan kapasitas cukup
            cursor.execute("""
                SELECT
                    F.kapasitas_max,
                    COALESCE(SUM(R.jumlah_tiket), 0) as tiket_terjual
                FROM
                    ATRAKSI A
                JOIN
                    FASILITAS F ON A.nama_atraksi = F.nama
                LEFT JOIN
                    RESERVASI R ON A.nama_atraksi = R.nama_atraksi
                    AND R.tanggal_kunjungan = %s
                    AND R.status != 'Cancelled'
                WHERE
                    A.nama_atraksi = %s
                GROUP BY
                    F.kapasitas_max
            """, [tanggal_kunjungan, nama_atraksi])
            
            kapasitas_data = cursor.fetchone()
            
            if not kapasitas_data:
                messages.error(request, "Atraksi tidak ditemukan.")
                return redirect('daftar_wahana_dan_atraksi')
            
            kapasitas_max = kapasitas_data[0]
            tiket_terjual = kapasitas_data[1]
            tiket_tersedia = kapasitas_max - tiket_terjual
            
            if int(jumlah_tiket) > tiket_tersedia:
                messages.error(request, f"Maaf, hanya tersisa {tiket_tersedia} tiket untuk tanggal ini.")
                
                # Ambil data atraksi
                cursor.execute("""
                    SELECT
                        A.nama_atraksi,
                        F.kapasitas_max,
                        A.lokasi,
                        F.jadwal
                    FROM
                        ATRAKSI A
                    JOIN
                        FASILITAS F ON A.nama_atraksi = F.nama
                    WHERE
                        A.nama_atraksi = %s
                """, [nama_atraksi])
                
                atraksi = cursor.fetchone()
                atraksi_data = {
                    'nama_atraksi': atraksi[0],
                    'kapasitas_max': atraksi[1],
                    'lokasi': atraksi[2],
                    'jadwal': atraksi[3]
                }
                
                from datetime import date
                today = date.today()
                
                return render(request, 'wahana_atraksi/tambah_reservasi.html', {
                    'atraksi': atraksi_data,
                    'form_data': {
                        'tanggal_kunjungan': tanggal_kunjungan,
                        'jumlah_tiket': jumlah_tiket
                    },
                    'tiket_tersedia': tiket_tersedia,
                    'today': today
                })
            
            # Buat reservasi baru
            cursor.execute("""
                INSERT INTO RESERVASI
                    (username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status)
                VALUES
                    (%s, %s, %s, %s, %s)
            """, [username, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status])
            
            messages.success(request, "Reservasi berhasil dibuat! Status: Pending")
            return redirect('detail_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)
    
    # Jika method GET tanpa nama_atraksi, redirect ke daftar
    return redirect('daftar_wahana_dan_atraksi')

# View untuk melihat detail reservasi
def detail_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh lihat
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    if current_user != username:
        # Bisa tambahkan pengecekan apakah user adalah admin
        messages.error(request, "Anda tidak memiliki akses untuk melihat reservasi ini.")
        return redirect('daftar_wahana_dan_atraksi')
    
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil detail reservasi
        cursor.execute("""
            SELECT
                r.username_p,
                r.nama_atraksi,
                a.lokasi,
                f.jadwal,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status
            FROM
                RESERVASI r
            JOIN
                ATRAKSI a ON r.nama_atraksi = a.nama_atraksi
            JOIN
                FASILITAS f ON a.nama_atraksi = f.nama
            WHERE
                r.username_p = %s
                AND r.nama_atraksi = %s
                AND r.tanggal_kunjungan = %s
        """, [username, nama_atraksi, tanggal_kunjungan])
        
        reservasi = cursor.fetchone()
        
        if not reservasi:
            raise Http404("Reservasi tidak ditemukan")
        
        reservasi_data = {
            'username_p': reservasi[0],
            'nama_atraksi': reservasi[1],
            'lokasi': reservasi[2],
            'jadwal': reservasi[3],
            'tanggal_kunjungan': reservasi[4],
            'jumlah_tiket': reservasi[5],
            'status': reservasi[6]
        }
    
    return render(request, 'wahana_atraksi/detail_reservasi.html', {
        'reservasi': reservasi_data
    })

# View untuk tampil form edit reservasi
def tampil_form_edit_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh edit
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    if current_user != username:
        # Bisa tambahkan pengecekan apakah user adalah admin
        messages.error(request, "Anda tidak memiliki akses untuk mengedit reservasi ini.")
        return redirect('daftar_wahana_dan_atraksi')
    
    # Jika method GET, tampilkan form edit
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil detail reservasi untuk ditampilkan di form
        cursor.execute("""
            SELECT
                r.username_p,
                r.nama_atraksi,
                a.lokasi,
                f.jadwal,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status
            FROM
                RESERVASI r
            JOIN
                ATRAKSI a ON r.nama_atraksi = a.nama_atraksi
            JOIN
                FASILITAS f ON a.nama_atraksi = f.nama
            WHERE
                r.username_p = %s
                AND r.nama_atraksi = %s
                AND r.tanggal_kunjungan = %s
        """, [username, nama_atraksi, tanggal_kunjungan])
        
        reservasi = cursor.fetchone()
        
        if not reservasi:
            raise Http404("Reservasi tidak ditemukan")
        
        reservasi_data = {
            'username_p': reservasi[0],
            'nama_atraksi': reservasi[1],
            'lokasi': reservasi[2],
            'jadwal': reservasi[3],
            'tanggal_kunjungan': reservasi[4],
            'jumlah_tiket': reservasi[5],
            'status': reservasi[6]
        }
    
    # Tambahkan tanggal hari ini untuk set min date input
    from datetime import date
    today = date.today()
    
    return render(request, 'wahana_atraksi/edit_reservasi.html', {
        'reservasi': reservasi_data,
        'today': today
    })

# View untuk mengedit reservasi
def edit_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh edit
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    if current_user != username:
        # Bisa tambahkan pengecekan apakah user adalah admin
        messages.error(request, "Anda tidak memiliki akses untuk mengedit reservasi ini.")
        return redirect('daftar_wahana_dan_atraksi')
    
    if request.method == "POST":
        jumlah_tiket = request.POST.get('jumlah_tiket')
        new_tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Jika tanggal berubah, perlu cek kapasitas di tanggal baru
            if new_tanggal_kunjungan != tanggal_kunjungan:
                # Cek kapasitas untuk tanggal baru
                cursor.execute("""
                    SELECT
                        F.kapasitas_max,
                        COALESCE(SUM(R.jumlah_tiket), 0) as tiket_terjual
                    FROM
                        ATRAKSI A
                    JOIN
                        FASILITAS F ON A.nama_atraksi = F.nama
                    LEFT JOIN
                        RESERVASI R ON A.nama_atraksi = R.nama_atraksi
                        AND R.tanggal_kunjungan = %s
                        AND R.status != 'Cancelled'
                    WHERE
                        A.nama_atraksi = %s
                    GROUP BY
                        F.kapasitas_max
                """, [new_tanggal_kunjungan, nama_atraksi])
                
                kapasitas_data = cursor.fetchone()
                
                if not kapasitas_data:
                    messages.error(request, "Atraksi tidak ditemukan.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)
                
                kapasitas_max = kapasitas_data[0]
                tiket_terjual = kapasitas_data[1]
                tiket_tersedia = kapasitas_max - tiket_terjual
                
                if int(jumlah_tiket) > tiket_tersedia:
                    messages.error(request, f"Maaf, hanya tersisa {tiket_tersedia} tiket untuk tanggal baru yang dipilih.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)
                
                # Hapus reservasi lama
                cursor.execute("""
                    DELETE FROM RESERVASI
                    WHERE username_p = %s
                    AND nama_atraksi = %s
                    AND tanggal_kunjungan = %s
                """, [username, nama_atraksi, tanggal_kunjungan])
                
                # Buat reservasi baru
                cursor.execute("""
                    INSERT INTO RESERVASI
                        (username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status)
                    VALUES
                        (%s, %s, %s, %s, 'Pending')
                """, [username, nama_atraksi, new_tanggal_kunjungan, jumlah_tiket])
                
                messages.success(request, "Reservasi berhasil diperbarui dengan tanggal kunjungan baru.")
                return redirect('detail_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=new_tanggal_kunjungan)
            
            else:
                # Jika hanya jumlah tiket yang berubah
                # Cek apakah masih ada tiket tersedia
                cursor.execute("""
                    SELECT
                        F.kapasitas_max,
                        COALESCE(SUM(R.jumlah_tiket), 0) as tiket_terjual
                    FROM
                        ATRAKSI A
                    JOIN
                        FASILITAS F ON A.nama_atraksi = F.nama
                    LEFT JOIN
                        RESERVASI R ON A.nama_atraksi = R.nama_atraksi
                        AND R.tanggal_kunjungan = %s
                        AND R.status != 'Cancelled'
                        AND NOT (R.username_p = %s AND R.nama_atraksi = %s AND R.tanggal_kunjungan = %s)
                    WHERE
                        A.nama_atraksi = %s
                    GROUP BY
                        F.kapasitas_max
                """, [tanggal_kunjungan, username, nama_atraksi, tanggal_kunjungan, nama_atraksi])
                
                kapasitas_data = cursor.fetchone()
                
                if not kapasitas_data:
                    messages.error(request, "Atraksi tidak ditemukan.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)
                
                kapasitas_max = kapasitas_data[0]
                tiket_terjual = kapasitas_data[1]
                tiket_tersedia = kapasitas_max - tiket_terjual

                if int(jumlah_tiket) > tiket_tersedia:
                    messages.error(request, f"Maaf, hanya tersisa {tiket_tersedia} tiket untuk tanggal ini.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)
                
                # Update jumlah tiket
                cursor.execute("""
                    UPDATE RESERVASI
                    SET jumlah_tiket = %s
                    WHERE username_p = %s
                    AND nama_atraksi = %s
                    AND tanggal_kunjungan = %s
                """, [jumlah_tiket, username, nama_atraksi, tanggal_kunjungan])
                
                messages.success(request, "Jumlah tiket berhasil diperbarui.")
                return redirect('detail_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)

    # Jika method GET, redirect ke form edit
    return redirect('tampil_form_edit_reservasi', username=username, nama_atraksi=nama_atraksi, tanggal_kunjungan=tanggal_kunjungan)

# View untuk membatalkan reservasi
def batalkan_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh membatalkan
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    if current_user != username:
        # Bisa tambahkan pengecekan apakah user adalah admin
        messages.error(request, "Anda tidak memiliki akses untuk membatalkan reservasi ini.")
        return redirect('daftar_wahana_dan_atraksi')
    
    # Konfirmasi via URL (mirip dengan delete wahana/atraksi)
    if request.method == "GET":
        # Langsung update status tanpa halaman konfirmasi tambahan
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Update status reservasi menjadi Cancelled
            cursor.execute("""
                UPDATE RESERVASI
                SET status = 'Cancelled'
                WHERE username_p = %s
                AND nama_atraksi = %s
                AND tanggal_kunjungan = %s
            """, [username, nama_atraksi, tanggal_kunjungan])
            
            messages.success(request, "Reservasi berhasil dibatalkan.")
    
    return redirect('daftar_wahana_dan_atraksi')