from django.shortcuts import render, redirect
from django.db import connection, transaction
from django.http import JsonResponse, Http404
from django.contrib import messages
import logging
import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Fungsi helper untuk cek apakah user adalah admin
def is_admin_user(username):
    """Helper function to check if user is admin"""
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        cursor.execute("""
            SELECT COUNT(*) FROM STAF_ADMIN WHERE username_sa = %s
        """, [username])
        result = cursor.fetchone()
        return result[0] > 0 if result else False

# View utama - menampilkan daftar wahana dan atraksi
def daftar_wahana_dan_atraksi(request):
    # Ambil username dari cookie
    username = request.COOKIES.get('user_id')
    
    if not username:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    is_admin = is_admin_user(username)
    
    # PEMISAHAN AKSES: Admin vs Pengunjung
    if is_admin:
        # ADMIN: Tampilkan panel admin lengkap dengan CRUD wahana/atraksi
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")  

            # Wahana untuk admin
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

            # Atraksi untuk admin
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
            
            # Semua reservasi untuk admin - UPDATE: gunakan nama_fasilitas
            cursor.execute("""
                SELECT
                    r.username_p,
                    r.nama_fasilitas,
                    CASE 
                        WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                        WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                        ELSE 'unknown'
                    END as jenis_fasilitas,
                    r.tanggal_kunjungan,
                    r.jumlah_tiket,
                    r.status
                FROM
                    RESERVASI r
                LEFT JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
                LEFT JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
                ORDER BY
                    r.tanggal_kunjungan DESC
            """)
            
            all_reservasi_columns = [col[0] for col in cursor.description]
            all_reservasi_rows = cursor.fetchall()
            all_reservasi_list = [dict(zip(all_reservasi_columns, row)) for row in all_reservasi_rows]

        return render(request, 'wahana_atraksi/daftar_wahana_dan_atraksi_admin.html', {
            'wahana_list': wahana_list,
            'atraksi_list': atraksi_list,
            'all_reservasi_list': all_reservasi_list,
            'is_admin': True,
            'is_logged_in': bool(username)
        })
    
    else:
        # PENGUNJUNG: Redirect ke halaman khusus pengunjung
        # Tidak boleh lihat tabel wahana/atraksi dengan tombol CRUD
        return redirect('pengunjung_reservasi')

# View untuk halaman pengunjung melihat list reservasi dan membuat reservasi baru
def pengunjung_reservasi(request):
    # Ambil username dari cookie
    username = request.COOKIES.get('user_id')
    
    if not username:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")  

        # Ambil data atraksi untuk list reservasi
        cursor.execute("""
            SELECT 
                A.nama_atraksi,
                F.kapasitas_max,
                A.lokasi,
                F.jadwal,
                (F.kapasitas_max - COALESCE(SUM(R.jumlah_tiket), 0)) AS kapasitas_tersedia
            FROM 
                ATRAKSI A
            JOIN 
                FASILITAS F ON A.nama_atraksi = F.nama
            LEFT JOIN 
                RESERVASI R ON A.nama_atraksi = R.nama_fasilitas 
                AND R.tanggal_kunjungan = CURRENT_DATE
                AND R.status != 'Cancelled'
            GROUP BY 
                A.nama_atraksi, F.kapasitas_max, A.lokasi, F.jadwal
            ORDER BY 
                A.nama_atraksi
        """)
        atraksi_columns = [col[0] for col in cursor.description]
        atraksi_rows = cursor.fetchall()
        atraksi_list = [dict(zip(atraksi_columns, row)) for row in atraksi_rows]

        # Ambil data wahana untuk list reservasi
        cursor.execute("""
            SELECT
                W.nama_wahana,
                F.kapasitas_max,
                F.jadwal,
                W.peraturan,
                (F.kapasitas_max - COALESCE(SUM(R.jumlah_tiket), 0)) AS kapasitas_tersedia
            FROM
                WAHANA W
            JOIN
                FASILITAS F ON W.nama_wahana = F.nama
            LEFT JOIN 
                RESERVASI R ON W.nama_wahana = R.nama_fasilitas 
                AND R.tanggal_kunjungan = CURRENT_DATE
                AND R.status != 'Cancelled'
            GROUP BY 
                W.nama_wahana, F.kapasitas_max, F.jadwal, W.peraturan
            ORDER BY
                W.nama_wahana
        """)
        wahana_columns = [col[0] for col in cursor.description]
        wahana_rows = cursor.fetchall()
        wahana_list = [dict(zip(wahana_columns, row)) for row in wahana_rows]
        
        # Reservasi milik user yang login - UPDATE: gunakan nama_fasilitas
        cursor.execute("""
            SELECT
                r.username_p,
                CONCAT(p.nama_depan, ' ', COALESCE(p.nama_tengah || ' ', ''), p.nama_belakang) AS nama_pengunjung,
                r.nama_fasilitas,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN a.lokasi
                    ELSE NULL
                END as lokasi,
                CASE 
                    WHEN w.nama_wahana IS NOT NULL THEN w.peraturan
                    ELSE NULL
                END as peraturan,
                f.jadwal,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                    WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                    ELSE 'unknown'
                END as jenis_fasilitas
            FROM
                RESERVASI r
            LEFT JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
            LEFT JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
            JOIN FASILITAS f ON r.nama_fasilitas = f.nama
            JOIN PENGUNJUNG pg ON r.username_p = pg.username_P
            JOIN PENGGUNA p ON pg.username_P = p.username
            WHERE
                r.username_p = %s
            ORDER BY
                r.tanggal_kunjungan DESC
        """, [username])
        
        reservasi_columns = [col[0] for col in cursor.description]
        reservasi_rows = cursor.fetchall()
        reservasi_list = [dict(zip(reservasi_columns, row)) for row in reservasi_rows]

    return render(request, 'wahana_atraksi/pengunjung_reservasi.html', {
        'atraksi_list': atraksi_list,
        'wahana_list': wahana_list,
        'reservasi_list': reservasi_list,
        'is_logged_in': True
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
def edit_wahana(request, nama_wahana):
    if request.method == 'POST':
        kapasitas_max = request.POST.get('kapasitas_max')
        jadwal_time = request.POST.get('jadwal')
        
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        jadwal_timestamp = f"{today} {jadwal_time}:00"

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            cursor.execute("""
                UPDATE FASILITAS SET kapasitas_max = %s, jadwal = %s WHERE nama = %s
            """, [kapasitas_max, jadwal_timestamp, nama_wahana])

            if 'peraturan[]' in request.POST:
                peraturan = request.POST.getlist('peraturan[]')
                peraturan_clean = [p.strip() for p in peraturan if p.strip()]
                
                if peraturan_clean:
                    peraturan_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(peraturan_clean)])
                else:
                    peraturan_str = ""
                
                cursor.execute("""
                    UPDATE WAHANA SET peraturan = %s WHERE nama_wahana = %s
                """, [peraturan_str, nama_wahana])

        messages.success(request, f'Wahana "{nama_wahana}" berhasil diupdate.')
        return redirect('daftar_wahana_dan_atraksi')
    
    else:
        wahana = {}
        
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
            
            import datetime
            jadwal = row[2]
            if isinstance(jadwal, datetime.datetime):
                jadwal_time = jadwal.strftime('%H:%M')
            else:
                try:
                    parsed_datetime = datetime.strptime(str(jadwal), '%Y-%m-%d %H:%M:%S')
                    jadwal_time = parsed_datetime.strftime('%H:%M')
                except:
                    jadwal_time = str(jadwal)
                
            wahana = {
                'nama_wahana': row[0],
                'kapasitas_max': row[1],
                'jadwal': jadwal_time,
                'peraturan': row[3] or "",
                'peraturan_list': []
            }
            
            if wahana['peraturan'] and wahana['peraturan'].strip():
                peraturan_lines = wahana['peraturan'].strip().split('\n')
                for line in peraturan_lines:
                    line = line.strip()
                    if line:
                        if '. ' in line:
                            parts = line.split('. ', 1)
                            if len(parts) == 2 and parts[0].isdigit():
                                wahana['peraturan_list'].append(parts[1].strip())
                            else:
                                wahana['peraturan_list'].append(line)
                        else:
                            wahana['peraturan_list'].append(line)
        
        return render(request, 'wahana_atraksi/edit_wahana.html', {
            'wahana': wahana
        })

# Delete Wahana
def delete_wahana(request, nama_wahana):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # CEK APAKAH ADA DI TABEL WAHANA
            cursor.execute("SELECT nama_wahana FROM WAHANA WHERE nama_wahana = %s", [nama_wahana])
            if not cursor.fetchone():
                messages.error(request, f"'{nama_wahana}' tidak ditemukan di tabel WAHANA")
                return redirect('daftar_wahana_dan_atraksi')
            
            cursor.execute("BEGIN;")
            
            try:
                print(f"Menghapus WAHANA: '{nama_wahana}'")
                
                # 1. Hapus reservasi untuk wahana ini
                cursor.execute("DELETE FROM RESERVASI WHERE nama_fasilitas = %s", [nama_wahana])
                deleted_reservasi = cursor.rowcount
                print(f"Deleted from RESERVASI: {deleted_reservasi} rows")
                
                # 2. Hapus dari WAHANA saja
                cursor.execute("DELETE FROM WAHANA WHERE nama_wahana = %s", [nama_wahana])
                deleted_wahana = cursor.rowcount
                print(f"Deleted from WAHANA: {deleted_wahana} rows")
                
                # 3. CEK apakah masih ada di ATRAKSI sebelum hapus FASILITAS
                cursor.execute("SELECT nama_atraksi FROM ATRAKSI WHERE nama_atraksi = %s", [nama_wahana])
                masih_ada_atraksi = cursor.fetchone()
                
                if not masih_ada_atraksi:
                    # Kalau tidak ada di atraksi, hapus dari FASILITAS juga
                    cursor.execute("DELETE FROM FASILITAS WHERE nama = %s", [nama_wahana])
                    deleted_fasilitas = cursor.rowcount
                    print(f"Deleted from FASILITAS: {deleted_fasilitas} rows")
                    messages.success(request, f"WAHANA '{nama_wahana}' berhasil dihapus sepenuhnya!")
                else:
                    # Kalau masih ada di atraksi, jangan hapus FASILITAS
                    messages.success(request, f"WAHANA '{nama_wahana}' berhasil dihapus")
                
                cursor.execute("COMMIT;")
                
            except Exception as inner_e:
                cursor.execute("ROLLBACK;")
                raise inner_e
                
    except Exception as e:
        print(f"Error deleting wahana: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        
    return redirect('daftar_wahana_dan_atraksi')

# Tambah Atraksi dengan pengecekan duplikasi
# ===== FULL CODE tambah_atraksi dengan Rotasi Pelatih =====

def tambah_atraksi(request):
    if request.method == "POST":
        nama_atraksi = request.POST['nama_atraksi']
        lokasi = request.POST['lokasi']
        kapasitas_max = request.POST['kapasitas_max']
        jadwal_datetime = request.POST['jadwal']
        
        # Konversi format datetime dari form ke format database
        # Format dari form: 'YYYY-MM-DDTHH:MM' (datetime-local input)
        # Format untuk database: 'YYYY-MM-DD HH:MM:SS'
        import datetime
        try:
            # Parse datetime dari form
            jadwal_obj = datetime.datetime.fromisoformat(jadwal_datetime)
            jadwal_timestamp = jadwal_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Fallback jika format tidak sesuai
            jadwal_timestamp = jadwal_datetime
        
        pelatih_terpilih = request.POST.getlist('pelatih[]')
        hewan_terlibat = request.POST.getlist('hewan[]')
        
        print(f"DEBUG: Selected pelatih: {pelatih_terpilih}")  # Debug
        print(f"DEBUG: Jadwal timestamp: {jadwal_timestamp}")  # Debug
        
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
                        'jadwal': jadwal_datetime,  # Tetap gunakan format datetime-local
                        'pelatih_ids': pelatih_terpilih,
                        'hewan_ids': hewan_terlibat
                    }
                })
            
            try:
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
                
                # Setup untuk menangkap rotation messages
                rotation_messages = []
                
                # Insert ke tabel JADWAL_PENUGASAN untuk setiap pelatih yang dipilih
                # Gunakan jadwal_timestamp dari input user, bukan CURRENT_TIMESTAMP
                for pelatih_username in pelatih_terpilih:
                    print(f"DEBUG: Assigning pelatih {pelatih_username} to {nama_atraksi} with date {jadwal_timestamp}")
                    
                    try:
                        # Clear previous notices
                        if hasattr(connection.connection, 'notices'):
                            connection.connection.notices.clear()
                        
                        cursor.execute("""
                            INSERT INTO JADWAL_PENUGASAN
                                (username_lh, nama_atraksi, tgl_penugasan)
                            VALUES (%s, %s, %s)
                        """, [pelatih_username, nama_atraksi, jadwal_timestamp])
                        
                        # Cek apakah ada NOTICE message dari trigger rotasi
                        if hasattr(connection.connection, 'notices'):
                            for notice in connection.connection.notices:
                                notice_msg = str(notice).strip()
                                if 'SUKSES:' in notice_msg and 'bertugas lebih dari 3 bulan' in notice_msg:
                                    rotation_messages.append(notice_msg)
                                    print(f"DEBUG: Rotation notice captured - {notice_msg}")
                        
                        print(f"DEBUG: Successfully assigned pelatih {pelatih_username} with date {jadwal_timestamp}")
                        
                    except Exception as pelatih_error:
                        print(f"DEBUG: Error assigning pelatih {pelatih_username}: {str(pelatih_error)}")
                        # Continue dengan pelatih lainnya jika ada error
                        continue
                
                # Insert ke tabel BERPARTISIPASI untuk hewan-hewan yang terlibat
                for hewan_id in hewan_terlibat:
                    cursor.execute("""
                        INSERT INTO BERPARTISIPASI
                            (id_hewan, nama_fasilitas)
                        VALUES (%s, %s)
                    """, [hewan_id, nama_atraksi])
                
                # Tampilkan pesan rotasi jika ada
                for msg in rotation_messages:
                    messages.success(request, msg)
                    print(f"DEBUG: Added rotation message to Django messages: {msg}")
                
                # Pesan sukses umum
                if rotation_messages:
                    messages.info(request, f"Atraksi '{nama_atraksi}' berhasil ditambahkan dengan rotasi pelatih!")
                else:
                    messages.success(request, f"Atraksi '{nama_atraksi}' berhasil ditambahkan!")
                
                print(f"DEBUG: Atraksi {nama_atraksi} successfully created")
                
            except Exception as e:
                print(f"DEBUG: Error during insert: {str(e)}")
                # Rollback otomatis karena menggunakan with connection.cursor()
                messages.error(request, f"Terjadi kesalahan: {str(e)}")
                return redirect('tambah_atraksi')
            
        return redirect('daftar_wahana_dan_atraksi')
    
    # GET request - tampilkan form
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
# ===== GANTI FUNCTION edit_atraksi YANG ADA DENGAN INI =====

def edit_atraksi(request, nama_atraksi):
    if request.method == 'POST':
        # Hanya ambil field yang boleh diedit
        kapasitas_max = request.POST.get('kapasitas_max')
        jadwal_datetime = request.POST.get('jadwal')
        
        # Konversi format datetime dari form ke format database
        import datetime
        try:
            jadwal_obj = datetime.datetime.fromisoformat(jadwal_datetime)
            jadwal_timestamp = jadwal_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            jadwal_timestamp = jadwal_datetime
        
        print(f"DEBUG: Updating atraksi {nama_atraksi} with jadwal: {jadwal_timestamp}")
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Update FASILITAS untuk kapasitas dan jadwal
            cursor.execute("""
                UPDATE FASILITAS 
                SET kapasitas_max = %s, jadwal = %s 
                WHERE nama = %s
            """, [kapasitas_max, jadwal_timestamp, nama_atraksi])
            
            print(f"DEBUG: Updated FASILITAS for {nama_atraksi}")
            
            # PERBAIKAN: Ambil pelatih yang sedang bertugas (yang terbaru)
            cursor.execute("""
                SELECT username_lh, tgl_penugasan
                FROM JADWAL_PENUGASAN 
                WHERE nama_atraksi = %s 
                ORDER BY tgl_penugasan DESC
                LIMIT 1
            """, [nama_atraksi])
            
            current_assignment = cursor.fetchone()
            
            if current_assignment:
                current_pelatih = current_assignment[0]
                current_date = current_assignment[1]
                
                print(f"DEBUG: Current pelatih: {current_pelatih}, assigned at: {current_date}")
                
                # PERBAIKAN: Cek apakah sudah ada assignment dengan timestamp yang sama
                cursor.execute("""
                    SELECT COUNT(*) FROM JADWAL_PENUGASAN
                    WHERE username_lh = %s AND tgl_penugasan = %s
                """, [current_pelatih, jadwal_timestamp])
                
                existing_count = cursor.fetchone()[0]
                
                if existing_count == 0:
                    # Tidak ada conflict, aman untuk insert
                    try:
                        # Clear previous notices untuk menangkap rotation messages
                        if hasattr(connection.connection, 'notices'):
                            connection.connection.notices.clear()
                        
                        cursor.execute("""
                            INSERT INTO JADWAL_PENUGASAN 
                            (username_lh, nama_atraksi, tgl_penugasan)
                            VALUES (%s, %s, %s)
                        """, [current_pelatih, nama_atraksi, jadwal_timestamp])
                        
                        print(f"DEBUG: Successfully inserted new assignment for {current_pelatih}")
                        
                        # Cek apakah ada rotasi yang terjadi (dari NOTICE messages)
                        rotation_happened = False
                        rotation_messages = []
                        if hasattr(connection.connection, 'notices'):
                            for notice in connection.connection.notices:
                                notice_msg = str(notice).strip()
                                if 'SUKSES:' in notice_msg and 'bertugas lebih dari 3 bulan' in notice_msg:
                                    rotation_messages.append(notice_msg)
                                    rotation_happened = True
                                    print(f"DEBUG: Rotation detected - {notice_msg}")
                        
                        if rotation_happened:
                            # ROTASI DIPERLUKAN - Ganti pelatih
                            print(f"DEBUG: Performing trainer rotation for {current_pelatih}")
                            
                            # 1. Hapus SEMUA assignment pelatih lama di atraksi ini
                            cursor.execute("""
                                DELETE FROM JADWAL_PENUGASAN 
                                WHERE nama_atraksi = %s 
                                AND username_lh = %s
                            """, [nama_atraksi, current_pelatih])
                            
                            print(f"DEBUG: Deleted all old assignments for {current_pelatih}")
                            
                            # 2. Pilih pelatih baru yang tidak conflict
                            cursor.execute("""
                                SELECT PH.username_lh,
                                       TRIM(CONCAT(P.nama_depan, ' ', 
                                           COALESCE(P.nama_tengah || ' ', ''), 
                                           P.nama_belakang)) AS nama_lengkap
                                FROM PELATIH_HEWAN PH
                                JOIN PENGGUNA P ON PH.username_lh = P.username
                                WHERE PH.username_lh != %s
                                AND NOT EXISTS (
                                    SELECT 1 FROM JADWAL_PENUGASAN JP 
                                    WHERE JP.username_lh = PH.username_lh 
                                    AND JP.tgl_penugasan = %s
                                )
                                ORDER BY RANDOM()
                                LIMIT 1
                            """, [current_pelatih, jadwal_timestamp])
                            
                            new_pelatih = cursor.fetchone()
                            
                            if new_pelatih:
                                # 3. Assign pelatih baru
                                cursor.execute("""
                                    INSERT INTO JADWAL_PENUGASAN 
                                    (username_lh, nama_atraksi, tgl_penugasan)
                                    VALUES (%s, %s, %s)
                                """, [new_pelatih[0], nama_atraksi, jadwal_timestamp])
                                
                                # Tampilkan pesan rotasi
                                for msg in rotation_messages:
                                    messages.success(request, msg)
                                
                                messages.info(request, 
                                    f'Pelatih baru "{new_pelatih[1]}" telah ditugaskan menggantikan yang lama.')
                                
                                print(f"DEBUG: Successfully assigned new trainer {new_pelatih[1]}")
                            else:
                                messages.warning(request, "Rotasi diperlukan tapi tidak ada pelatih pengganti tersedia.")
                        else:
                            # TIDAK ADA ROTASI - Cleanup assignment lama saja
                            cursor.execute("""
                                DELETE FROM JADWAL_PENUGASAN 
                                WHERE nama_atraksi = %s 
                                AND username_lh = %s
                                AND tgl_penugasan < %s
                            """, [nama_atraksi, current_pelatih, jadwal_timestamp])
                            
                            print(f"DEBUG: Cleaned up old assignments, kept latest for {current_pelatih}")
                        
                        # Pesan sukses
                        if rotation_happened:
                            messages.info(request, f'Jadwal atraksi "{nama_atraksi}" berhasil diupdate dengan rotasi pelatih.')
                        else:
                            # Ambil nama pelatih untuk pesan
                            cursor.execute("""
                                SELECT TRIM(CONCAT(P.nama_depan, ' ', 
                                       COALESCE(P.nama_tengah || ' ', ''), 
                                       P.nama_belakang)) AS nama_lengkap
                                FROM PENGGUNA P 
                                WHERE P.username = %s
                            """, [current_pelatih])
                            
                            result = cursor.fetchone()
                            current_pelatih_nama = result[0] if result else current_pelatih
                            
                            messages.success(request, 
                                f'Atraksi "{nama_atraksi}" berhasil diupdate. '
                                f'Jadwal penugasan pelatih "{current_pelatih_nama}" telah diperbarui.')
                        
                    except Exception as e:
                        print(f"DEBUG: Error during assignment update: {str(e)}")
                        
                        # PERBAIKAN: Jika ada duplicate key error, update saja
                        if 'duplicate key' in str(e).lower():
                            cursor.execute("""
                                UPDATE JADWAL_PENUGASAN 
                                SET nama_atraksi = %s
                                WHERE username_lh = %s AND tgl_penugasan = %s
                            """, [nama_atraksi, current_pelatih, jadwal_timestamp])
                            
                            messages.success(request, f'Atraksi "{nama_atraksi}" berhasil diupdate.')
                            print(f"DEBUG: Updated existing assignment instead of inserting")
                        else:
                            messages.error(request, f"Terjadi kesalahan saat update penugasan: {str(e)}")
                else:
                    # Sudah ada assignment dengan timestamp yang sama, update saja
                    cursor.execute("""
                        UPDATE JADWAL_PENUGASAN 
                        SET nama_atraksi = %s
                        WHERE username_lh = %s AND tgl_penugasan = %s
                    """, [nama_atraksi, current_pelatih, jadwal_timestamp])
                    
                    messages.success(request, f'Atraksi "{nama_atraksi}" berhasil diupdate (assignment sudah ada).')
                    print(f"DEBUG: Updated existing assignment for {current_pelatih}")
                    
            else:
                # Tidak ada pelatih yang bertugas, assign pelatih random baru
                cursor.execute("""
                    SELECT PH.username_lh,
                           TRIM(CONCAT(P.nama_depan, ' ', 
                               COALESCE(P.nama_tengah || ' ', ''), 
                               P.nama_belakang)) AS nama_lengkap
                    FROM PELATIH_HEWAN PH
                    JOIN PENGGUNA P ON PH.username_lh = P.username
                    WHERE NOT EXISTS (
                        SELECT 1 FROM JADWAL_PENUGASAN JP 
                        WHERE JP.username_lh = PH.username_lh 
                        AND JP.tgl_penugasan = %s
                    )
                    ORDER BY RANDOM()
                    LIMIT 1
                """, [jadwal_timestamp])
                
                new_pelatih = cursor.fetchone()
                if new_pelatih:
                    cursor.execute("""
                        INSERT INTO JADWAL_PENUGASAN 
                        (username_lh, nama_atraksi, tgl_penugasan)
                        VALUES (%s, %s, %s)
                    """, [new_pelatih[0], nama_atraksi, jadwal_timestamp])
                    
                    messages.success(request, 
                        f'Atraksi "{nama_atraksi}" berhasil diupdate. '
                        f'Pelatih "{new_pelatih[1]}" telah ditugaskan.')
                    
                    print(f"DEBUG: Assigned new trainer {new_pelatih[1]} with date {jadwal_timestamp}")
                else:
                    messages.warning(request, 
                        f'Atraksi "{nama_atraksi}" berhasil diupdate, namun tidak ada pelatih yang tersedia.')

        return redirect('daftar_wahana_dan_atraksi')
    
    else:
        # GET request - tampilkan form edit (kode yang sama seperti sebelumnya)
        atraksi = {}
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
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
                
            import datetime
            jadwal = row[3]
            if isinstance(jadwal, datetime.datetime):
                jadwal_datetime = jadwal.strftime('%Y-%m-%dT%H:%M')
            else:
                try:
                    parsed_datetime = datetime.datetime.strptime(str(jadwal), '%Y-%m-%d %H:%M:%S')
                    jadwal_datetime = parsed_datetime.strftime('%Y-%m-%dT%H:%M')
                except:
                    jadwal_datetime = str(jadwal)
                
            atraksi = {
                'nama_atraksi': row[0],
                'kapasitas_max': row[1],
                'lokasi': row[2],
                'jadwal': jadwal_datetime
            }
            
            cursor.execute("""
                SELECT
                    TRIM(CONCAT(P.nama_depan, ' ', 
                        COALESCE(P.nama_tengah || ' ', ''), 
                        P.nama_belakang)) AS nama_lengkap,
                    JP.tgl_penugasan
                FROM
                    JADWAL_PENUGASAN JP
                JOIN 
                    PENGGUNA P ON JP.username_lh = P.username
                WHERE
                    JP.nama_atraksi = %s
                ORDER BY JP.tgl_penugasan DESC
            """, [nama_atraksi])
            
            current_pelatih = cursor.fetchall()
            atraksi['current_pelatih'] = [
                {
                    'nama': row[0], 
                    'tgl_penugasan': row[1].strftime('%d %B %Y, %H:%M') if row[1] else '-'
                } 
                for row in current_pelatih
            ]
            
            cursor.execute("""
                SELECT
                    H.nama, H.spesies
                FROM
                    BERPARTISIPASI B
                JOIN
                    HEWAN H ON B.id_hewan = H.id
                WHERE
                    B.nama_fasilitas = %s
            """, [nama_atraksi])
            
            current_hewan = cursor.fetchall()
            atraksi['current_hewan'] = [
                {'nama': row[0], 'spesies': row[1]} 
                for row in current_hewan
            ]
        
        return render(request, 'wahana_atraksi/edit_atraksi.html', {
            'atraksi': atraksi
        })
    
# Delete Atraksi
def delete_atraksi(request, nama_atraksi):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # CEK APAKAH INI BENAR-BENAR ATRAKSI (bukan wahana)
            cursor.execute("SELECT nama_atraksi FROM ATRAKSI WHERE nama_atraksi = %s", [nama_atraksi])
            if not cursor.fetchone():
                messages.error(request, f"'{nama_atraksi}' tidak ditemukan di tabel ATRAKSI")
                return redirect('daftar_wahana_dan_atraksi')
            
            # CEK APAKAH JUGA ADA DI WAHANA
            cursor.execute("SELECT nama_wahana FROM WAHANA WHERE nama_wahana = %s", [nama_atraksi])
            ada_di_wahana = cursor.fetchone()
            
            if ada_di_wahana:
                messages.error(request, f"ERROR: '{nama_atraksi}' ada di kedua tabel ATRAKSI dan WAHANA. Tidak bisa dihapus sampai duplikasi ini diperbaiki!")
                return redirect('daftar_wahana_dan_atraksi')
            
            cursor.execute("BEGIN;")
            
            try:
                # 1. Hapus referensi
                cursor.execute("DELETE FROM RESERVASI WHERE nama_fasilitas = %s", [nama_atraksi])
                cursor.execute("DELETE FROM BERPARTISIPASI WHERE nama_fasilitas = %s", [nama_atraksi])
                cursor.execute("DELETE FROM JADWAL_PENUGASAN WHERE nama_atraksi = %s", [nama_atraksi])
                
                # 2. Hapus dari ATRAKSI saja (bukan WAHANA)
                cursor.execute("DELETE FROM ATRAKSI WHERE nama_atraksi = %s", [nama_atraksi])
                
                # 3. JANGAN hapus dari FASILITAS kalau masih ada di WAHANA
                cursor.execute("COMMIT;")
                
                messages.success(request, f"Atraksi '{nama_atraksi}' berhasil dihapus!")
                
            except Exception as inner_e:
                cursor.execute("ROLLBACK;")
                raise inner_e
                
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        
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

# View untuk menampilkan form reservasi wahana
def tampil_form_reservasi_wahana(request, nama_wahana):
    # Ambil username dari cookie
    username = request.COOKIES.get('user_id')
        
    if not username:
        return redirect('login')
    
    # Ambil data wahana
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
        
        wahana = cursor.fetchone()
        
        if not wahana:
            raise Http404("Wahana tidak ditemukan")
        
        wahana_data = {
            'nama_wahana': wahana[0],
            'kapasitas_max': wahana[1],
            'jadwal': wahana[2],
            'peraturan': wahana[3]
        }
    
    from datetime import date
    today = date.today()
    
    return render(request, 'wahana_atraksi/form_reservasi_wahana.html', {
        'wahana': wahana_data,
        'today': today
    })

# View untuk membuat reservasi baru
# ===== GANTI FUNCTION buat_reservasi YANG ADA DENGAN INI =====

def buat_reservasi(request):
    username = request.COOKIES.get('user_id')
    
    if not username:
        return redirect('login')
    
    if request.method == "POST":
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
        jumlah_tiket = int(request.POST.get('jumlah_tiket', 1))
        
        # DEBUG: Print data yang diterima
        print(f"DEBUG - buat_reservasi:")
        print(f"Username: {username}")
        print(f"Nama Atraksi: {nama_atraksi}")
        print(f"Tanggal: {tanggal_kunjungan}")
        print(f"Jumlah Tiket: {jumlah_tiket}")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO SIZOPI;")
                
                # IMPORTANT: Pastikan stored procedure menggunakan nama_fasilitas
                cursor.execute("""
                    SELECT buat_reservasi_dengan_check(%s, %s, %s, %s)
                """, [username, nama_atraksi, tanggal_kunjungan, jumlah_tiket])
                
                result = cursor.fetchone()[0]
                print(f"DEBUG - Stored procedure result: {result}")
                
                if result.startswith('ERROR:'):
                    # Handle error dari stored procedure
                    cursor.execute("""
                        SELECT A.nama_atraksi, F.kapasitas_max, A.lokasi, F.jadwal
                        FROM ATRAKSI A
                        JOIN FASILITAS F ON A.nama_atraksi = F.nama
                        WHERE A.nama_atraksi = %s
                    """, [nama_atraksi])
                    
                    atraksi = cursor.fetchone()
                    if atraksi:
                        atraksi_data = {
                            'nama_atraksi': atraksi[0],
                            'kapasitas_max': atraksi[1],
                            'lokasi': atraksi[2],
                            'jadwal': atraksi[3]
                        }
                    else:
                        atraksi_data = {}
                    
                    from datetime import date
                    today = date.today()
                    
                    return render(request, 'wahana_atraksi/tambah_reservasi.html', {
                        'error_message': result,
                        'atraksi': atraksi_data,
                        'form_data': {
                            'tanggal_kunjungan': tanggal_kunjungan,
                            'jumlah_tiket': jumlah_tiket
                        },
                        'today': today
                    })
                else:
                    # BERHASIL - Verifikasi apakah data benar-benar tersimpan
                    cursor.execute("""
                        SELECT COUNT(*) FROM RESERVASI 
                        WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
                    """, [username, nama_atraksi, tanggal_kunjungan])
                    
                    count = cursor.fetchone()[0]
                    print(f"DEBUG - Jumlah reservasi yang ditemukan setelah insert: {count}")
                    
                    if count > 0:
                        messages.success(request, result)
                        # REDIRECT ke halaman pengunjung untuk menghindari error detail
                        return redirect('detail_reservasi', 
                                        username=username, 
                                        nama_fasilitas=nama_atraksi, 
                                        tanggal_kunjungan=tanggal_kunjungan)
                    else:
                        # Data tidak tersimpan, kemungkinan ada masalah dengan trigger/stored procedure
                        messages.error(request, "Reservasi gagal disimpan. Silakan coba lagi.")
                        return redirect('tampil_form_reservasi', nama_atraksi=nama_atraksi)
                    
        except Exception as e:
            print(f"DEBUG - Exception: {str(e)}")
            error_message = str(e)
            
            # Ambil data atraksi untuk ditampilkan kembali
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO SIZOPI;")
                cursor.execute("""
                    SELECT A.nama_atraksi, F.kapasitas_max, A.lokasi, F.jadwal
                    FROM ATRAKSI A
                    JOIN FASILITAS F ON A.nama_atraksi = F.nama
                    WHERE A.nama_atraksi = %s
                """, [nama_atraksi])
                
                atraksi = cursor.fetchone()
                if atraksi:
                    atraksi_data = {
                        'nama_atraksi': atraksi[0],
                        'kapasitas_max': atraksi[1],
                        'lokasi': atraksi[2],
                        'jadwal': atraksi[3]
                    }
                else:
                    atraksi_data = {}
            
            from datetime import date
            today = date.today()
            
            return render(request, 'wahana_atraksi/tambah_reservasi.html', {
                'error_message': error_message,
                'atraksi': atraksi_data,
                'form_data': {
                    'tanggal_kunjungan': tanggal_kunjungan,
                    'jumlah_tiket': jumlah_tiket
                },
                'today': today
            })
    
    return redirect('pengunjung_reservasi')
# View untuk membuat reservasi wahana
# ===== GANTI FUNCTION buat_reservasi_wahana YANG ADA DENGAN INI =====

def buat_reservasi_wahana(request):
    username = request.COOKIES.get('user_id')
    
    if not username:
        return redirect('login')
    
    if request.method == "POST":
        nama_wahana = request.POST.get('nama_wahana')
        tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
        jumlah_tiket = int(request.POST.get('jumlah_tiket', 1))
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO SIZOPI;")
                
                # UPDATE: Panggil stored procedure dengan nama_fasilitas (wahana)
                cursor.execute("""
                    SELECT buat_reservasi_dengan_check(%s, %s, %s, %s)
                """, [username, nama_wahana, tanggal_kunjungan, jumlah_tiket])
                
                result = cursor.fetchone()[0]
                
                if result.startswith('ERROR:'):
                    # Ambil data wahana untuk ditampilkan kembali
                    cursor.execute("""
                        SELECT W.nama_wahana, F.kapasitas_max, F.jadwal, W.peraturan
                        FROM WAHANA W
                        JOIN FASILITAS F ON W.nama_wahana = F.nama
                        WHERE W.nama_wahana = %s
                    """, [nama_wahana])
                    
                    wahana_row = cursor.fetchone()
                    if wahana_row:
                        wahana = {
                            'nama_wahana': wahana_row[0],
                            'kapasitas_max': wahana_row[1],
                            'jadwal': wahana_row[2],
                            'peraturan': wahana_row[3]
                        }
                    else:
                        wahana = {}
                    
                    from datetime import date
                    today = date.today()
                    
                    return render(request, 'wahana_atraksi/form_reservasi_wahana.html', {
                        'error_message': result,
                        'wahana': wahana,
                        'form_data': {
                            'tanggal_kunjungan': tanggal_kunjungan,
                            'jumlah_tiket': jumlah_tiket
                        },
                        'today': today
                    })
                else:
                    messages.success(request, result)
                    return redirect('detail_reservasi', 
                                  username=username, 
                                  nama_fasilitas=nama_wahana, 
                                  tanggal_kunjungan=tanggal_kunjungan)
                    
        except Exception as e:
            error_message = str(e)
            
            # Ambil data wahana untuk ditampilkan kembali
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO SIZOPI;")
                cursor.execute("""
                    SELECT W.nama_wahana, F.kapasitas_max, F.jadwal, W.peraturan
                    FROM WAHANA W
                    JOIN FASILITAS F ON W.nama_wahana = F.nama
                    WHERE W.nama_wahana = %s
                """, [nama_wahana])
                
                wahana_row = cursor.fetchone()
                if wahana_row:
                    wahana = {
                        'nama_wahana': wahana_row[0],
                        'kapasitas_max': wahana_row[1],
                        'jadwal': wahana_row[2],
                        'peraturan': wahana_row[3]
                    }
                else:
                    wahana = {}
            
            from datetime import date
            today = date.today()
            
            return render(request, 'wahana_atraksi/form_reservasi_wahana.html', {
                'error_message': error_message,
                'wahana': wahana,
                'form_data': {
                    'tanggal_kunjungan': tanggal_kunjungan,
                    'jumlah_tiket': jumlah_tiket
                },
                'today': today
            })
    
    return redirect('pengunjung_reservasi')
# View untuk melihat detail reservasi
def detail_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh lihat
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        # Jika belum login, redirect ke halaman login
        return redirect('login')
    
    is_admin = is_admin_user(current_user)
    
    if not is_admin and current_user != username:
        messages.error(request, "Anda tidak memiliki akses untuk melihat reservasi ini.")
        return redirect('pengunjung_reservasi')
    
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # UPDATE: Ambil detail reservasi dengan nama_fasilitas
        cursor.execute("""
            SELECT
                r.username_p,
                r.nama_fasilitas,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN a.lokasi
                    ELSE NULL
                END as lokasi,
                CASE 
                    WHEN w.nama_wahana IS NOT NULL THEN w.peraturan
                    ELSE NULL
                END as peraturan,
                f.jadwal,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                    WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                    ELSE 'unknown'
                END as jenis_fasilitas
            FROM
                RESERVASI r
            LEFT JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
            LEFT JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
            JOIN FASILITAS f ON r.nama_fasilitas = f.nama
            WHERE
                r.username_p = %s
                AND r.nama_fasilitas = %s
                AND r.tanggal_kunjungan = %s
        """, [username, nama_fasilitas, tanggal_kunjungan])
        
        reservasi = cursor.fetchone()
        
        if not reservasi:
            raise Http404("Reservasi tidak ditemukan")
        
        # Buat data reservasi yang konsisten
        reservasi_data = {
            'username_p': reservasi[0],
            'nama_fasilitas': reservasi[1],
            'lokasi': reservasi[2] if reservasi[8] == 'atraksi' else None,
            'peraturan': reservasi[3] if reservasi[8] == 'wahana' else None,
            'jadwal': reservasi[4],
            'tanggal_kunjungan': reservasi[5],
            'jumlah_tiket': reservasi[6],
            'status': reservasi[7],
            'jenis_fasilitas': reservasi[8],
            # Untuk kompatibilitas dengan template lama
            'nama_atraksi': reservasi[1] if reservasi[8] == 'atraksi' else None,
            'nama_wahana': reservasi[1] if reservasi[8] == 'wahana' else None,
        }
    
    return render(request, 'wahana_atraksi/detail_reservasi.html', {
        'reservasi': reservasi_data
    })

# View untuk tampil form edit reservasi
def tampil_form_edit_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh edit
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        return redirect('login')
    
    is_admin = is_admin_user(current_user)
    
    if not is_admin and current_user != username:
        messages.error(request, "Anda tidak memiliki akses untuk mengedit reservasi ini.")
        return redirect('pengunjung_reservasi')
    
    # Jika method GET, tampilkan form edit
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # UPDATE: Ambil detail reservasi dengan nama_fasilitas
        cursor.execute("""
            SELECT
                r.username_p,
                r.nama_fasilitas,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN a.lokasi
                    ELSE NULL
                END as lokasi,
                CASE 
                    WHEN w.nama_wahana IS NOT NULL THEN w.peraturan
                    ELSE NULL
                END as peraturan,
                f.jadwal,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                    WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                    ELSE 'unknown'
                END as jenis_fasilitas
            FROM
                RESERVASI r
            LEFT JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
            LEFT JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
            JOIN FASILITAS f ON r.nama_fasilitas = f.nama
            WHERE
                r.username_p = %s
                AND r.nama_fasilitas = %s
                AND r.tanggal_kunjungan = %s
        """, [username, nama_fasilitas, tanggal_kunjungan])
        
        reservasi = cursor.fetchone()
        
        if not reservasi:
            raise Http404("Reservasi tidak ditemukan")
        
        # Buat data reservasi yang konsisten
        reservasi_data = {
            'username_p': reservasi[0],
            'nama_fasilitas': reservasi[1],
            'lokasi': reservasi[2] if reservasi[8] == 'atraksi' else None,
            'peraturan': reservasi[3] if reservasi[8] == 'wahana' else None,
            'jadwal': reservasi[4],
            'tanggal_kunjungan': reservasi[5],
            'jumlah_tiket': reservasi[6],
            'status': reservasi[7],
            'jenis_fasilitas': reservasi[8],
            # Untuk kompatibilitas dengan template lama
            'nama_atraksi': reservasi[1] if reservasi[8] == 'atraksi' else None,
            'nama_wahana': reservasi[1] if reservasi[8] == 'wahana' else None,
        }
    
    # Tambahkan tanggal hari ini untuk set min date input
    from datetime import date
    today = date.today()
    
    return render(request, 'wahana_atraksi/edit_reservasi.html', {
        'reservasi': reservasi_data,
        'today': today
    })

# View untuk mengedit reservasi
def edit_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh edit
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        return redirect('login')
    
    is_admin = is_admin_user(current_user)
    
    if not is_admin and current_user != username:
        messages.error(request, "Anda tidak memiliki akses untuk mengedit reservasi ini.")
        return redirect('pengunjung_reservasi')
    
    if request.method == "POST":
        jumlah_tiket = request.POST.get('jumlah_tiket')
        new_tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # Jika tanggal berubah, perlu cek kapasitas di tanggal baru
            if new_tanggal_kunjungan != tanggal_kunjungan:
                # Cek apakah ini atraksi atau wahana
                cursor.execute("""
                    SELECT COUNT(*) FROM ATRAKSI WHERE nama_atraksi = %s
                """, [nama_fasilitas])
                
                is_atraksi = cursor.fetchone()[0] > 0
                
                # UPDATE: Cek kapasitas dengan nama_fasilitas
                cursor.execute("""
                    SELECT
                        F.kapasitas_max,
                        COALESCE(SUM(R.jumlah_tiket), 0) as tiket_terjual
                    FROM
                        FASILITAS F
                    LEFT JOIN
                        RESERVASI R ON F.nama = R.nama_fasilitas
                        AND R.tanggal_kunjungan = %s
                        AND R.status != 'Cancelled'
                    WHERE
                        F.nama = %s
                    GROUP BY
                        F.kapasitas_max
                """, [new_tanggal_kunjungan, nama_fasilitas])
                
                kapasitas_data = cursor.fetchone()
                
                if not kapasitas_data:
                    messages.error(request, "Fasilitas tidak ditemukan.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)
                
                kapasitas_max = kapasitas_data[0]
                tiket_terjual = kapasitas_data[1]
                tiket_tersedia = kapasitas_max - tiket_terjual
                
                if int(jumlah_tiket) > tiket_tersedia:
                    messages.error(request, f"Maaf, hanya tersisa {tiket_tersedia} tiket untuk tanggal baru yang dipilih.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)
                
                # UPDATE: Hapus dan buat reservasi baru dengan nama_fasilitas
                cursor.execute("""
                    DELETE FROM RESERVASI
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [username, nama_fasilitas, tanggal_kunjungan])
                
                cursor.execute("""
                    INSERT INTO RESERVASI
                        (username_p, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status)
                    VALUES
                        (%s, %s, %s, %s, 'Pending')
                """, [username, nama_fasilitas, new_tanggal_kunjungan, jumlah_tiket])
                
                messages.success(request, "Reservasi berhasil diperbarui dengan tanggal kunjungan baru.")
                return redirect('detail_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=new_tanggal_kunjungan)
            
            else:
                # Jika hanya jumlah tiket yang berubah - UPDATE: cek dengan nama_fasilitas
                cursor.execute("""
                    SELECT
                        F.kapasitas_max,
                        COALESCE(SUM(R.jumlah_tiket), 0) as tiket_terjual
                    FROM
                        FASILITAS F
                    LEFT JOIN
                        RESERVASI R ON F.nama = R.nama_fasilitas
                        AND R.tanggal_kunjungan = %s
                        AND R.status != 'Cancelled'
                        AND NOT (R.username_p = %s AND R.nama_fasilitas = %s AND R.tanggal_kunjungan = %s)
                    WHERE
                        F.nama = %s
                    GROUP BY
                        F.kapasitas_max
                """, [tanggal_kunjungan, username, nama_fasilitas, tanggal_kunjungan, nama_fasilitas])
                
                kapasitas_data = cursor.fetchone()
                
                if not kapasitas_data:
                    messages.error(request, "Fasilitas tidak ditemukan.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)
                
                kapasitas_max = kapasitas_data[0]
                tiket_terjual = kapasitas_data[1]
                tiket_tersedia = kapasitas_max - tiket_terjual

                if int(jumlah_tiket) > tiket_tersedia:
                    messages.error(request, f"Maaf, hanya tersisa {tiket_tersedia} tiket untuk tanggal ini.")
                    return redirect('tampil_form_edit_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)
                
                # UPDATE: Update jumlah tiket dengan nama_fasilitas
                cursor.execute("""
                    UPDATE RESERVASI
                    SET jumlah_tiket = %s
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [jumlah_tiket, username, nama_fasilitas, tanggal_kunjungan])
                
                messages.success(request, "Jumlah tiket berhasil diperbarui.")
                return redirect('detail_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)

    # Jika method GET, redirect ke form edit
    return redirect('tampil_form_edit_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)

# View untuk membatalkan reservasi
def batalkan_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek hak akses - hanya pemilik reservasi atau admin yang boleh membatalkan
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        return redirect('login')
    
    is_admin = is_admin_user(current_user)
    
    if not is_admin and current_user != username:
        messages.error(request, "Anda tidak memiliki akses untuk membatalkan reservasi ini.")
        return redirect('pengunjung_reservasi')
    
    # Konfirmasi via URL (mirip dengan delete wahana/atraksi)
    if request.method == "GET":
        # Langsung update status tanpa halaman konfirmasi tambahan
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # UPDATE: Update status reservasi dengan nama_fasilitas
            cursor.execute("""
                UPDATE RESERVASI
                SET status = 'Cancelled'
                WHERE username_p = %s
                AND nama_fasilitas = %s
                AND tanggal_kunjungan = %s
            """, [username, nama_fasilitas, tanggal_kunjungan])
            
            messages.success(request, "Reservasi berhasil dibatalkan.")
    
    return redirect('pengunjung_reservasi')

# View untuk admin edit reservasi
def admin_edit_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek apakah user adalah admin
    current_user = request.COOKIES.get('user_id')
    
    if not current_user or not is_admin_user(current_user):
        messages.error(request, "Anda tidak memiliki akses admin.")
        return redirect('daftar_wahana_dan_atraksi')
    
    if request.method == 'POST':
        jumlah_tiket = request.POST.get('jumlah_tiket')
        new_tanggal_kunjungan = request.POST.get('tanggal_kunjungan')
        
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            if new_tanggal_kunjungan != tanggal_kunjungan:
                # UPDATE: Cek kapasitas dengan nama_fasilitas
                cursor.execute("""
                    SELECT
                        F.kapasitas_max,
                        COALESCE(SUM(R.jumlah_tiket), 0) as tiket_terjual
                    FROM
                        FASILITAS F
                    LEFT JOIN
                        RESERVASI R ON F.nama = R.nama_fasilitas
                        AND R.tanggal_kunjungan = %s
                        AND R.status != 'Cancelled'
                    WHERE
                        F.nama = %s
                    GROUP BY
                        F.kapasitas_max
                """, [new_tanggal_kunjungan, nama_fasilitas])
                
                kapasitas_data = cursor.fetchone()
                kapasitas_max = kapasitas_data[0]
                tiket_terjual = kapasitas_data[1]
                tiket_tersedia = kapasitas_max - tiket_terjual
                
                if int(jumlah_tiket) > tiket_tersedia:
                    messages.error(request, f"Kapasitas tidak mencukupi. Tersisa {tiket_tersedia} tiket.")
                    return redirect('admin_edit_reservasi', username=username, nama_fasilitas=nama_fasilitas, tanggal_kunjungan=tanggal_kunjungan)
                
                # UPDATE: Hapus dan buat reservasi baru dengan nama_fasilitas
                cursor.execute("""
                    DELETE FROM RESERVASI
                    WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
                """, [username, nama_fasilitas, tanggal_kunjungan])
                
                cursor.execute("""
                    INSERT INTO RESERVASI (username_p, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status)
                    VALUES (%s, %s, %s, %s, 'Confirmed')
                """, [username, nama_fasilitas, new_tanggal_kunjungan, jumlah_tiket])
                
                messages.success(request, "Reservasi berhasil diperbarui oleh admin.")
                return redirect('daftar_wahana_dan_atraksi')
            else:
                # UPDATE: Update jumlah tiket dengan nama_fasilitas
                cursor.execute("""
                    UPDATE RESERVASI
                    SET jumlah_tiket = %s, status = 'Confirmed'
                    WHERE username_p = %s AND nama_fasilitas = %s AND tanggal_kunjungan = %s
                """, [jumlah_tiket, username, nama_fasilitas, tanggal_kunjungan])
                
                messages.success(request, "Reservasi berhasil diperbarui oleh admin.")
                return redirect('daftar_wahana_dan_atraksi')
    
    # GET request - tampilkan form edit
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # UPDATE: Ambil reservasi dengan nama_fasilitas
        cursor.execute("""
            SELECT
                r.username_p,
                r.nama_fasilitas,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN a.lokasi
                    ELSE NULL
                END as lokasi,
                CASE 
                    WHEN w.nama_wahana IS NOT NULL THEN w.peraturan
                    ELSE NULL
                END as peraturan,
                f.jadwal,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status,
                CASE 
                    WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                    WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                    ELSE 'unknown'
                END as jenis_fasilitas
            FROM
                RESERVASI r
            LEFT JOIN ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
            LEFT JOIN WAHANA w ON r.nama_fasilitas = w.nama_wahana
            JOIN FASILITAS f ON r.nama_fasilitas = f.nama
            WHERE
                r.username_p = %s
                AND r.nama_fasilitas = %s
                AND r.tanggal_kunjungan = %s
        """, [username, nama_fasilitas, tanggal_kunjungan])
        
        reservasi = cursor.fetchone()
        
        if not reservasi:
            raise Http404("Reservasi tidak ditemukan")
        
        # Buat data reservasi yang konsisten
        reservasi_data = {
            'username_p': reservasi[0],
            'nama_fasilitas': reservasi[1],
            'lokasi': reservasi[2] if reservasi[8] == 'atraksi' else None,
            'peraturan': reservasi[3] if reservasi[8] == 'wahana' else None,
            'jadwal': reservasi[4],
            'tanggal_kunjungan': reservasi[5],
            'jumlah_tiket': reservasi[6],
            'status': reservasi[7],
            'jenis_fasilitas': reservasi[8],
            # Untuk kompatibilitas dengan template lama
            'nama_atraksi': reservasi[1] if reservasi[8] == 'atraksi' else None,
            'nama_wahana': reservasi[1] if reservasi[8] == 'wahana' else None,
        }
    
    from datetime import date
    today = date.today()
    
    return render(request, 'wahana_atraksi/admin_edit_reservasi.html', {
        'reservasi': reservasi_data,
        'today': today
    })


# View untuk admin batalkan reservasi
def admin_batalkan_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek apakah user adalah admin
    current_user = request.COOKIES.get('user_id')
    
    if not current_user or not is_admin_user(current_user):
        messages.error(request, "Anda tidak memiliki akses admin.")
        return redirect('daftar_wahana_dan_atraksi')
    
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # UPDATE: Update status dengan nama_fasilitas
            cursor.execute("""
                UPDATE RESERVASI
                SET status = 'Cancelled'
                WHERE username_p = %s
                AND nama_fasilitas = %s
                AND tanggal_kunjungan = %s
            """, [username, nama_fasilitas, tanggal_kunjungan])
            
            messages.success(request, "Reservasi berhasil dibatalkan oleh admin.")
        
        return redirect('daftar_wahana_dan_atraksi')
    
    # GET request - tampilkan konfirmasi
    return render(request, 'wahana_atraksi/admin_batalkan_reservasi.html', {
        'username': username,
        'nama_fasilitas': nama_fasilitas,
        'tanggal_kunjungan': tanggal_kunjungan
    })


# View untuk konfirmasi pembatalan reservasi dengan halaman khusus
def konfirmasi_batalkan_reservasi(request, username, nama_fasilitas, tanggal_kunjungan):
    # Cek hak akses
    current_user = request.COOKIES.get('user_id')
    
    if not current_user:
        return redirect('login')
    
    is_admin = is_admin_user(current_user)
    
    if not is_admin and current_user != username:
        messages.error(request, "Anda tidak memiliki akses untuk membatalkan reservasi ini.")
        return redirect('pengunjung_reservasi')
    
    # Ambil data reservasi untuk ditampilkan
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # UPDATE: Query dengan nama_fasilitas
        cursor.execute("""
            SELECT
                r.username_p,
                r.nama_fasilitas,
                r.tanggal_kunjungan,
                r.jumlah_tiket,
                r.status
            FROM
                RESERVASI r
            WHERE
                r.username_p = %s
                AND r.nama_fasilitas = %s
                AND r.tanggal_kunjungan = %s
        """, [username, nama_fasilitas, tanggal_kunjungan])
        
        reservasi = cursor.fetchone()
        
        if not reservasi:
            raise Http404("Reservasi tidak ditemukan")
        
        reservasi_data = {
            'username_p': reservasi[0],
            'nama_fasilitas': reservasi[1],
            'tanggal_kunjungan': reservasi[2],
            'jumlah_tiket': reservasi[3],
            'status': reservasi[4]
        }
    
    if request.method == "POST":
        # Proses pembatalan
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO SIZOPI;")
            
            # UPDATE: Update dengan nama_fasilitas
            cursor.execute("""
                UPDATE RESERVASI
                SET status = 'Cancelled'
                WHERE username_p = %s
                AND nama_fasilitas = %s
                AND tanggal_kunjungan = %s
            """, [username, nama_fasilitas, tanggal_kunjungan])
            
            messages.success(request, "Reservasi berhasil dibatalkan.")
        
        if is_admin:
            return redirect('daftar_wahana_dan_atraksi')
        else:
            return redirect('pengunjung_reservasi')
    
    return render(request, 'wahana_atraksi/batalkan_reservasi.html', {
        'reservasi': reservasi_data
    })


# ===== TAMBAHKAN FUNCTIONS INI DI BAGIAN ATAS SETELAH IMPORT =====

def check_kapasitas_atraksi(nama_atraksi, tanggal_kunjungan, jumlah_tiket_diminta):
    """
    Mengecek apakah kapasitas atraksi mencukupi untuk reservasi
    Returns: (is_available, message, sisa_kapasitas)
    """
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil kapasitas maksimum atraksi
        cursor.execute("""
            SELECT F.kapasitas_max
            FROM FASILITAS F
            WHERE F.nama = %s
        """, [nama_atraksi])
        
        kapasitas_result = cursor.fetchone()
        if not kapasitas_result:
            return False, f"ERROR: Atraksi '{nama_atraksi}' tidak ditemukan.", 0
        
        kapasitas_max = kapasitas_result[0]
        
        # UPDATE: Hitung total tiket dengan nama_fasilitas
        cursor.execute("""
            SELECT COALESCE(SUM(jumlah_tiket), 0) as total_reserved
            FROM RESERVASI
            WHERE nama_fasilitas = %s 
            AND tanggal_kunjungan = %s
            AND status != 'Cancelled'
        """, [nama_atraksi, tanggal_kunjungan])
        
        reserved_result = cursor.fetchone()
        total_reserved = reserved_result[0] if reserved_result else 0
        
        # Hitung sisa kapasitas
        sisa_kapasitas = kapasitas_max - total_reserved
        
        # Cek apakah kapasitas mencukupi
        if jumlah_tiket_diminta > sisa_kapasitas:
            message = f'ERROR: Kapasitas tersisa "{sisa_kapasitas}" tiket, atraksi tidak mencukupi untuk sejumlah "{jumlah_tiket_diminta}" tiket yang diminta.'
            return False, message, sisa_kapasitas
        
        return True, "Kapasitas mencukupi", sisa_kapasitas

def check_kapasitas_wahana(nama_wahana, tanggal_kunjungan, jumlah_tiket_diminta):
    """
    Mengecek apakah kapasitas wahana mencukupi untuk reservasi
    Returns: (is_available, message, sisa_kapasitas)
    """
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO SIZOPI;")
        
        # Ambil kapasitas maksimum wahana
        cursor.execute("""
            SELECT F.kapasitas_max
            FROM FASILITAS F
            WHERE F.nama = %s
        """, [nama_wahana])
        
        kapasitas_result = cursor.fetchone()
        if not kapasitas_result:
            return False, f"ERROR: Wahana '{nama_wahana}' tidak ditemukan.", 0
        
        kapasitas_max = kapasitas_result[0]
        
        # UPDATE: Hitung total tiket dengan nama_fasilitas
        cursor.execute("""
            SELECT COALESCE(SUM(jumlah_tiket), 0) as total_reserved
            FROM RESERVASI
            WHERE nama_fasilitas = %s 
            AND tanggal_kunjungan = %s
            AND status != 'Cancelled'
        """, [nama_wahana, tanggal_kunjungan])
        
        reserved_result = cursor.fetchone()
        total_reserved = reserved_result[0] if reserved_result else 0
        
        # Hitung sisa kapasitas
        sisa_kapasitas = kapasitas_max - total_reserved
        
        # Cek apakah kapasitas mencukupi
        if jumlah_tiket_diminta > sisa_kapasitas:
            message = f'ERROR: Kapasitas tersisa "{sisa_kapasitas}" tiket, wahana tidak mencukupi untuk sejumlah "{jumlah_tiket_diminta}" tiket yang diminta.'
            return False, message, sisa_kapasitas
        
        return True, "Kapasitas mencukupi", sisa_kapasitas

def capture_postgres_notices(cursor):
    """
    Helper function untuk menangkap NOTICE messages dari PostgreSQL
    """
    notices = []
    try:
        if hasattr(cursor.connection, 'notices'):
            for notice in cursor.connection.notices:
                notice_msg = str(notice.message if hasattr(notice, 'message') else notice).strip()
                if notice_msg and 'SUKSES:' in notice_msg:
                    notices.append(notice_msg)
            # Clear notices setelah diambil
            cursor.connection.notices.clear()
    except Exception as e:
        print(f"DEBUG: Error capturing notices: {str(e)}")
    return notices

# Tambahkan views ini di akhir file views.py Anda

def redirect_old_detail_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    """
    Redirect URL lama (dengan nama_atraksi) ke URL baru (dengan nama_fasilitas)
    """
    return redirect('detail_reservasi', 
                   username=username, 
                   nama_fasilitas=nama_atraksi,  # nama_atraksi di URL lama jadi nama_fasilitas di URL baru
                   tanggal_kunjungan=tanggal_kunjungan)

def redirect_old_edit_reservasi(request, username, nama_atraksi, tanggal_kunjungan):
    """
    Redirect URL lama (dengan nama_atraksi) ke URL baru (dengan nama_fasilitas)
    """
    return redirect('tampil_form_edit_reservasi', 
                   username=username, 
                   nama_fasilitas=nama_atraksi,  # nama_atraksi di URL lama jadi nama_fasilitas di URL baru
                   tanggal_kunjungan=tanggal_kunjungan)