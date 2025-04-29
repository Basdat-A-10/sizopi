from django.shortcuts import render
from django.db import connection
from datetime import date

def dashboard_view(request):
    dokter = fetch_one("""
        SELECT pengguna.username, pengguna.nama_depan, pengguna.nama_tengah, pengguna.nama_belakang, pengguna.email, pengguna.no_telepon
        FROM sizopi.dokter_hewan
        JOIN sizopi.pengguna ON dokter_hewan.username_dh = pengguna.username
        LIMIT 1
    """)
    
    if dokter is None:
        return render(request, 'dashboard/dashboard.html', {'error': 'Tidak ada Dokter Hewan ditemukan.'})
    
    role = get_role(dokter['username'])

    dashboard_data = {
        'nama_lengkap': get_full_name(dokter),
        'username': dokter['username'],
        'email': dokter['email'],
        'no_telepon': dokter['no_telepon'],
        'peran': role,
    }

    if role == 'Pengunjung':
        pengunjung = fetch_one("""
            SELECT alamat, tgl_lahir
            FROM sizopi.pengunjung
            WHERE username_p = %s
        """, [dokter['username']])

        dashboard_data.update({
            'alamat': pengunjung['alamat'],
            'tgl_lahir': pengunjung['tgl_lahir'],
            'riwayat_kunjungan': get_riwayat_kunjungan(dokter['username']),
            'tiket_dibeli': get_informasi_tiket(dokter['username']),
        })

    elif role == 'Dokter Hewan':
        dokter_info = fetch_one("""
            SELECT no_str
            FROM sizopi.dokter_hewan
            WHERE username_dh = %s
        """, [dokter['username']])

        spesialisasi = fetch_all("""
            SELECT nama_spesialisasi
            FROM sizopi.spesialisasi
            WHERE username_sh = %s
        """, [dokter['username']])

        dashboard_data.update({
            'no_str': dokter_info['no_str'],
            'spesialisasi': [s['nama_spesialisasi'] for s in spesialisasi],
            'jumlah_hewan': get_jumlah_hewan_rekam_medis(dokter['username']),
        })

    elif role == 'Penjaga Hewan':
        penjaga = fetch_one("""
            SELECT id_staf
            FROM sizopi.penjaga_hewan
            WHERE username_jh = %s
        """, [dokter['username']])

        dashboard_data.update({
            'id_staf': penjaga['id_staf'],
            'jumlah_hewan_dipakan': get_jumlah_hewan_dipakan(penjaga['id_staf']),
        })

    elif role == 'Staf Admin':
        admin = fetch_one("""
            SELECT id_staf
            FROM sizopi.staf_admin
            WHERE username_sa = %s
        """, [dokter['username']])

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
        """, [dokter['username']])

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
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tanggal_kunjungan
            FROM sizopi.kunjungan
            WHERE username_pengunjung = %s
            ORDER BY tanggal_kunjungan DESC
        """, [username])
        rows = cursor.fetchall()
    return [row[0] for row in rows]

def get_informasi_tiket(username):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nomor_tiket, tanggal_pembelian
            FROM sizopi.tiket
            WHERE username_pembeli = %s
            ORDER BY tanggal_pembelian DESC
        """, [username])
        rows = cursor.fetchall()
    return [{'nomor_tiket': row[0], 'tanggal_pembelian': row[1]} for row in rows]

def get_jumlah_hewan_rekam_medis(username):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM sizopi.catatan_medis
            WHERE username_dh = %s
        """, [username])
        count = cursor.fetchone()[0]
    return count

def get_jumlah_hewan_dipakan(id_staf):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM sizopi.memberi
            WHERE id_staf_penjaga = %s
        """, [str(id_staf)])
        count = cursor.fetchone()[0]
    return count

def get_ringkasan_penjualan_tiket():
    today = date.today()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT SUM(harga)
            FROM sizopi.tiket
            WHERE tanggal_pembelian = %s
        """, [today])
        total = cursor.fetchone()[0]
    return total or 0

def get_jumlah_pengunjung_hari_ini():
    today = date.today()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT username_pengunjung)
            FROM sizopi.kunjungan
            WHERE tanggal_kunjungan = %s
        """, [today])
        count = cursor.fetchone()[0]
    return count

def get_laporan_pendapatan_mingguan():
    today = date.today()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tanggal_pembelian, SUM(harga)
            FROM sizopi.tiket
            WHERE tanggal_pembelian >= %s - INTERVAL '6 days'
            GROUP BY tanggal_pembelian
            ORDER BY tanggal_pembelian
        """, [today])
        rows = cursor.fetchall()
    return [{'tanggal': row[0], 'pendapatan': row[1]} for row in rows]

def get_jadwal_pertunjukan(id_staf):
    today = date.today()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama_pertunjukan, jam_mulai
            FROM sizopi.atraksi
            WHERE id_staf_pelatih = %s
            AND tanggal_pertunjukan = %s
            ORDER BY jam_mulai
        """, [str(id_staf), today])
        rows = cursor.fetchall()
    return [{'nama_pertunjukan': row[0], 'jam_mulai': row[1]} for row in rows]

def get_daftar_hewan_dilatih(id_staf):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama_hewan
            FROM sizopi.hewan
            WHERE id_pelatih = %s
        """, [str(id_staf)])
        rows = cursor.fetchall()
    return [row[0] for row in rows]

def get_status_latihan_terakhir(id_staf):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT status_terakhir
            FROM sizopi.latihan
            WHERE id_staf_pelatih = %s
            ORDER BY tanggal_latihan DESC, jam_latihan DESC
            LIMIT 1
        """, [str(id_staf)])
        result = cursor.fetchone()
    return result[0] if result else 'Belum Ada Latihan'
