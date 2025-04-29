from django.shortcuts import render
from django.db import connection
from datetime import date

def dashboard_view(request):
    # Username masih hardcode
    username = 'andrea_trainer'
    
    if not username:
        return render(request, 'dashboard/dashboard.html', {'error': 'Username tidak ditemukan.'})
    
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
                'riwayat_kunjungan': get_riwayat_kunjungan(username),
                'tiket_dibeli': get_informasi_tiket(username),
            })

    elif role == 'Dokter Hewan':
        dokter_info = fetch_one("""
            SELECT no_str
            FROM sizopi.dokter_hewan
            WHERE username_dh = %s
        """, [username])

        if dokter_info:
            spesialisasi = fetch_all("""
                SELECT nama_spesialisasi
                FROM sizopi.spesialisasi
                WHERE username_sh = %s
            """, [username])

            dashboard_data.update({
                'no_str': dokter_info['no_str'],
                'spesialisasi': [s['nama_spesialisasi'] for s in spesialisasi],
                'jumlah_hewan': get_jumlah_hewan_rekam_medis(username),
            })

    elif role == 'Penjaga Hewan':
        penjaga = fetch_one("""
            SELECT id_staf
            FROM sizopi.penjaga_hewan
            WHERE username_jh = %s
        """, [username])

        if penjaga:
            dashboard_data.update({
                'id_staf': penjaga['id_staf'],
                'jumlah_hewan_dipakan': get_jumlah_hewan_dipakan(username),
            })

    elif role == 'Staf Admin':
        admin = fetch_one("""
            SELECT id_staf
            FROM sizopi.staf_admin
            WHERE username_sa = %s
        """, [username])

        if admin:
            dashboard_data.update({
                'id_staf': admin['id_staf'],
                'penjualan_tiket_hari_ini': get_ringkasan_penjualan_tiket(),
                'jumlah_pengunjung_hari_ini': get_jumlah_pengunjung_hari_ini(),
                'laporan_pendapatan_mingguan': get_laporan_pendapatan_mingguan(),
            })

    elif role == 'Pelatih Hewan':
        pelatih = fetch_one("""
            SELECT id_staf
            FROM sizopi.pelatih_hewan
            WHERE username_lh = %s
        """, [username])

        if pelatih:
            dashboard_data.update({
                'id_staf': pelatih['id_staf'],
                'jadwal_pertunjukan_hari_ini': get_jadwal_pertunjukan(pelatih['id_staf']),
                'daftar_hewan_dilatih': get_daftar_hewan_dilatih(pelatih['id_staf']),
                'status_latihan_terakhir': get_status_latihan_terakhir(pelatih['id_staf']),
            })

    return render(request, 'dashboard/dashboard.html', {'dashboard_data': dashboard_data})


def fetch_one(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        desc = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        if row:
            return dict(zip(desc, row))
        return None

def fetch_all(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        desc = [col[0] for col in cursor.description]
        return [dict(zip(desc, row)) for row in cursor.fetchall()]

def get_full_name(user):
    return f"{user['nama_depan']} {user['nama_tengah'] or ''} {user['nama_belakang']}".strip()

def get_role(username):
    # detect role manually by checking existence
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

def get_riwayat_kunjungan(username):
    return []

def get_informasi_tiket(username):
    return []

def get_jumlah_hewan_rekam_medis(username):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM sizopi.catatan_medis
            WHERE username_dh = %s
        """, [username])
        count = cursor.fetchone()[0]
    return count

def get_jumlah_hewan_dipakan(username_penjaga):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM "sizopi"."memberi"
            WHERE username_jh = %s
        """, [username_penjaga])
        count = cursor.fetchone()[0]
    return count


def get_ringkasan_penjualan_tiket():
    return 0

def get_jumlah_pengunjung_hari_ini():
    return

def get_laporan_pendapatan_mingguan():
    return []

def get_jadwal_pertunjukan(id_staf):
    return []
def get_daftar_hewan_dilatih(id_staf):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama
            FROM sizopi.hewan
            WHERE id = %s
        """, [str(id_staf)])
        rows = cursor.fetchall()
    return [row[0] for row in rows]

def get_status_latihan_terakhir(id_staf):
    return []