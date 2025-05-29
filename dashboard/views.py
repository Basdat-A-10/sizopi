from django.shortcuts import render
from django.db import connection
from datetime import date


def dashboard_view(request):
    username = request.COOKIES.get('user_id')

    if not username:
        return render(request, 'dashboard/dashboard.html', {'error': 'Silakan login terlebih dahulu.'})

    user = fetch_one("""
        SELECT username, nama_depan, nama_tengah, nama_belakang, email, no_telepon
        FROM sizopi.pengguna
        WHERE username = %s
    """, [username])

    if user is None:
        return render(request, 'dashboard/dashboard.html', {'error': 'Pengguna tidak ditemukan.'})

    role = get_role(username)

    dashboard_data = {
        'nama_lengkap': get_full_name(user),
        'username': user['username'],
        'email': user['email'],
        'no_telepon': user['no_telepon'],
        'peran': role,
    }
    if role == 'Pelatih Hewan':
        pelatih_info = fetch_one("""
            SELECT id_staf
            FROM sizopi.pelatih_hewan
            WHERE username_lh = %s
        """, [username])

        jadwal_hari_ini = fetch_all("""
            SELECT jp.tgl_penugasan, a.nama_atraksi, a.lokasi
            FROM sizopi.jadwal_penugasan jp
            JOIN sizopi.atraksi a ON jp.nama_atraksi = a.nama_atraksi
            WHERE jp.username_lh = %s AND jp.tgl_penugasan = CURRENT_DATE
        """, [username])

        daftar_hewan = fetch_all("""
            SELECT DISTINCT h.nama
            FROM sizopi.jadwal_penugasan jp
            JOIN sizopi.berpartisipasi b ON jp.nama_atraksi = b.nama_fasilitas
            JOIN sizopi.hewan h ON h.id = b.id_hewan
            WHERE jp.username_lh = %s
        """, [username])

        status_latihan = fetch_one("""
            SELECT tgl_penugasan, nama_atraksi
            FROM sizopi.jadwal_penugasan
            WHERE username_lh = %s
            ORDER BY tgl_penugasan DESC
            LIMIT 1
        """, [username])
        status_str = (
            f"{status_latihan['tgl_penugasan']} - {status_latihan['nama_atraksi']}"
            if status_latihan else "Belum ada latihan"
        )

        dashboard_data.update({
            'id_staf': pelatih_info['id_staf'] if pelatih_info else None,
            'jadwal_pertunjukan_hari_ini': jadwal_hari_ini,
            'daftar_hewan_dilatih': [h['nama'] for h in daftar_hewan],
            'status_latihan_terakhir': status_str,
        })

    if role == 'Staf Admin':
        staf_admin_info = fetch_one("""
            SELECT id_staf
            FROM sizopi.staf_admin
            WHERE username_sa = %s
        """, [username])

        penjualan_hari_ini = fetch_one("""
            SELECT COALESCE(SUM(jumlah_tiket), 0) AS total_tiket
            FROM sizopi.reservasi
            WHERE tanggal_kunjungan = CURRENT_DATE
        """)

        pengunjung_hari_ini = fetch_one("""
            SELECT COUNT(DISTINCT username_p) AS total_pengunjung
            FROM sizopi.reservasi
            WHERE tanggal_kunjungan = CURRENT_DATE
        """)

        pendapatan_mingguan = fetch_all("""
            SELECT tanggal_kunjungan, SUM(jumlah_tiket) AS total_tiket
            FROM sizopi.reservasi
            WHERE tanggal_kunjungan >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY tanggal_kunjungan
            ORDER BY tanggal_kunjungan
        """)

        dashboard_data.update({
            'id_staf': staf_admin_info['id_staf'] if staf_admin_info else None,
            'penjualan_tiket_hari_ini': penjualan_hari_ini['total_tiket'] if penjualan_hari_ini else 0,
            'jumlah_pengunjung_hari_ini': pengunjung_hari_ini['total_pengunjung'] if pengunjung_hari_ini else 0,
            'laporan_pendapatan_mingguan': pendapatan_mingguan,
        })

        dashboard_data.update({
            'id_staf': staf_admin_info['id_staf'] if staf_admin_info else None,
            'penjualan_tiket_hari_ini': penjualan_hari_ini['total_tiket'] if penjualan_hari_ini else 0,
            'jumlah_pengunjung_hari_ini': pengunjung_hari_ini['total_pengunjung'] if pengunjung_hari_ini else 0,
            'laporan_pendapatan_mingguan': pendapatan_mingguan
        })

    if role == 'Penjaga Hewan':
        penjaga_info = fetch_one("""
            SELECT id_staf
            FROM sizopi.penjaga_hewan
            WHERE username_jh = %s
        """, [username])

        jumlah_hewan_dipakan = fetch_one("""
            SELECT COUNT(DISTINCT id_hewan) AS total
            FROM sizopi.memberi
            WHERE username_jh = %s
        """, [username])

        dashboard_data.update({
            'id_staf': penjaga_info['id_staf'] if penjaga_info else None,
            'jumlah_hewan_dipakan': jumlah_hewan_dipakan['total'] if jumlah_hewan_dipakan else 0
        })

    
    if role == 'Dokter Hewan':
        dokter_info = fetch_one("""
            SELECT no_str
            FROM sizopi.dokter_hewan
            WHERE username_dh = %s
        """, [username])
        
        spesialisasi = fetch_all("""
            SELECT nama_spesialisasi
            FROM sizopi.spesialisasi
            WHERE username_sh = %s
        """, [username])

        rekam_medis_count = fetch_one("""
            SELECT COUNT(DISTINCT id_hewan) AS total
            FROM sizopi.catatan_medis
            WHERE username_dh = %s
        """, [username])

        dashboard_data.update({
            'no_str': dokter_info['no_str'] if dokter_info else None,
            'spesialisasi': [row['nama_spesialisasi'] for row in spesialisasi],
            'jumlah_hewan': rekam_medis_count['total'] if rekam_medis_count else 0
        })


    if role == 'Pengunjung':
        pengunjung = fetch_one("""
            SELECT alamat, tgl_lahir
            FROM sizopi.pengunjung
            WHERE username_p = %s
        """, [username])

        if pengunjung:
            dashboard_data.update({
                'alamat': pengunjung['alamat'],
                'tgl_lahir': pengunjung['tgl_lahir'],
            })

        riwayat = fetch_all("""
            SELECT nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status
            FROM sizopi.reservasi
            WHERE username_p = %s
            ORDER BY tanggal_kunjungan DESC
        """, [username])
        dashboard_data['riwayat_kunjungan'] = riwayat

        tiket_info = fetch_one("""
            SELECT COUNT(*) AS jumlah_reservasi, COALESCE(SUM(jumlah_tiket), 0) AS total_tiket
            FROM sizopi.reservasi
            WHERE username_p = %s
        """, [username])
        dashboard_data['tiket_dibeli'] = [{'jumlah_tiket': tiket_info['total_tiket']}] if tiket_info else []

    return render(request, 'dashboard/dashboard.html', {'dashboard_data': dashboard_data})

def fetch_all(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def fetch_one(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        desc = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        return dict(zip(desc, row)) if row else None

def get_role(username):
    if fetch_one("SELECT 1 FROM sizopi.staf_admin WHERE username_sa = %s", [username]):
        return 'Staf Admin'
    if fetch_one("SELECT 1 FROM sizopi.dokter_hewan WHERE username_dh = %s", [username]):
        return 'Dokter Hewan'
    if fetch_one("SELECT 1 FROM sizopi.penjaga_hewan WHERE username_jh = %s", [username]):
        return 'Penjaga Hewan'
    if fetch_one("SELECT 1 FROM sizopi.pelatih_hewan WHERE username_lh = %s", [username]):
        return 'Pelatih Hewan'
    if fetch_one("SELECT 1 FROM sizopi.pengunjung WHERE username_p = %s", [username]):
        return 'Pengunjung'
    return 'User'

def get_full_name(user):
    return f"{user['nama_depan']} {user['nama_tengah'] or ''} {user['nama_belakang']}".strip()
