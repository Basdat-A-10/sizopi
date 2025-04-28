from django.shortcuts import render
from .models import (
    Pengguna, Pengunjung, DokterHewan, PenjagaHewan, PelatihHewan, StafAdmin, Spesialisasi
)
from django.db import connection
from django.db.models import Count, Sum
from django.utils.timezone import now
from datetime import date

def dashboard_view(request):
    dokter = DokterHewan.objects.first()
    if dokter is None:
        return render(request, 'dashboard/dashboard.html', {'error': 'Tidak ada Dokter Hewan ditemukan.'})

    pengguna = dokter.username_dh



    role = pengguna.get_role()

    dashboard_data = {
        'nama_lengkap': pengguna.get_full_name(),
        'username': pengguna.username,
        'email': pengguna.email,
        'no_telepon': pengguna.no_telepon,
        'peran': role,
    }

    if role == 'Pengunjung':
        pengunjung = Pengunjung.objects.get(pengguna=pengguna)
        dashboard_data.update({
            'alamat': pengunjung.alamat,
            'tgl_lahir': pengunjung.tgl_lahir,
            'riwayat_kunjungan': get_riwayat_kunjungan(pengguna.username),
            'tiket_dibeli': get_informasi_tiket(pengguna.username),
        })

    elif role == 'Dokter Hewan':
        dokter = DokterHewan.objects.get(username_dh=pengguna)
        dashboard_data.update({
            'no_str': dokter.no_str,
            'spesialisasi': list(Spesialisasi.objects.filter(username_sh=dokter).values_list('nama_spesialisasi', flat=True)),
            'jumlah_hewan': get_jumlah_hewan_rekam_medis(pengguna.username),
        })

    elif role == 'Penjaga Hewan':
        penjaga = PenjagaHewan.objects.get(pengguna=pengguna)
        dashboard_data.update({
            'id_staf': penjaga.id_staf,
            'jumlah_hewan_dipakan': get_jumlah_hewan_dipakan(penjaga.id_staf),
        })

    elif role == 'Staf Admin':
        admin = StafAdmin.objects.get(pengguna=pengguna)
        dashboard_data.update({
            'id_staf': admin.id_staf,
            'penjualan_tiket_hari_ini': get_ringkasan_penjualan_tiket(),
            'jumlah_pengunjung_hari_ini': get_jumlah_pengunjung_hari_ini(),
            'laporan_pendapatan_mingguan': get_laporan_pendapatan_mingguan(),
        })

    elif role == 'Pelatih Hewan':
        pelatih = PelatihHewan.objects.get(pengguna=pengguna)
        dashboard_data.update({
            'id_staf': pelatih.id_staf,
            'jadwal_pertunjukan_hari_ini': get_jadwal_pertunjukan(pelatih.id_staf),
            'daftar_hewan_dilatih': get_daftar_hewan_dilatih(pelatih.id_staf),
            'status_latihan_terakhir': get_status_latihan_terakhir(pelatih.id_staf),
        })

    return render(request, 'dashboard/dashboard.html', {'dashboard_data': dashboard_data})

# --------------------------------------------------------------------
# 🔥 Helper functions (FINISHED, ready to run)

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
