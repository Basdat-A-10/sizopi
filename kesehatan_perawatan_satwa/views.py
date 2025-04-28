from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from datetime import datetime
from django.db import connection
import uuid

def index(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role')
    }
    return render(request, 'kesehatan_perawatan_satwa/index.html', context)

# ===== REKAM MEDIS =====

def rekam_medis(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    username_dh = request.COOKIES.get('user_id')
    
    # Data dummy, fallback n test
    dummy_data = [{
        'id_hewan': 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
        'nama_hewan': 'Raja',
        'spesies': 'Panthera tigris sumatrae',
        'tanggal_pemeriksaan': datetime.strptime('2023-09-15', '%Y-%m-%d'),
        'tanggal_str': '2023-09-15',
        'status_pemeriksaan': 'Pemulihan',
        'diagnosis': 'Infeksi kulit ringan',
        'pengobatan': 'Antibiotik dan salep antijamur',
        'catatan_tindak_lanjut': 'Evaluasi ulang dalam 2 minggu, pantau perkembangan luka',
        'nama_dokter': 'Ajeng Kusuma Pratiwi'
    }]
    
    rekam_medis_data = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    cm.tanggal_pemeriksaan,
                    cm.status_kesehatan,
                    cm.diagnosis,
                    cm.pengobatan,
                    cm.catatan_tindak_lanjut,
                    p.nama_depan || ' ' || COALESCE(p.nama_tengah || ' ', '') || p.nama_belakang as nama_dokter
                FROM 
                    SIZOPI.CATATAN_MEDIS cm
                    JOIN SIZOPI.HEWAN h ON cm.id_hewan = h.id
                    JOIN SIZOPI.DOKTER_HEWAN dh ON cm.username_dh = dh.username_DH
                    JOIN SIZOPI.PENGGUNA p ON dh.username_DH = p.username
                ORDER BY 
                    cm.tanggal_pemeriksaan DESC
            """)
            
            rows = cursor.fetchall()
            for row in rows:
                if row[0] and row[3]:  
                    tanggal_obj = row[3]
                    tanggal_str = tanggal_obj.strftime('%Y-%m-%d') if tanggal_obj else ''
                    
                    rekam_medis_data.append({
                        'id_hewan': row[0],
                        'nama_hewan': row[1],
                        'spesies': row[2],
                        'tanggal_pemeriksaan': tanggal_obj,
                        'tanggal_str': tanggal_str,
                        'status_pemeriksaan': row[4],
                        'diagnosis': row[5],
                        'pengobatan': row[6],
                        'catatan_tindak_lanjut': row[7],
                        'nama_dokter': row[8],
                    })
    except Exception as e:
        rekam_medis_data = dummy_data  # data dummy jika db error (for test only)
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'rekam_medis_data': rekam_medis_data,
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/index.html', context)

def tambah_rekam_medis(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    username_dh = request.COOKIES.get('user_id')
    
    if request.method == 'POST':
        try:
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
            status_kesehatan = request.POST.get('status_kesehatan')
            diagnosis = request.POST.get('diagnosis')
            pengobatan = request.POST.get('pengobatan')
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut')
            
            with connection.cursor() as cursor:
                # Cek apakah sudah ada rekam medis pada tanggal yang sama untuk hewan tersebut
                cursor.execute("""
                    SELECT 1
                    FROM SIZOPI.CATATAN_MEDIS
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])
                
                if cursor.fetchone():
                    return redirect('kesehatan_perawatan_satwa:tambah_rekam_medis')
                
                # Tambahkan rekam medis baru
                cursor.execute("""
                    INSERT INTO SIZOPI.CATATAN_MEDIS
                    (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut])
                
                # Update status kesehatan hewan
                cursor.execute("""
                    UPDATE SIZOPI.HEWAN
                    SET status_kesehatan = %s
                    WHERE id = %s
                """, [status_kesehatan, id_hewan])
            
            return redirect('kesehatan_perawatan_satwa:rekam_medis')
            
        except Exception as e:
            return redirect('kesehatan_perawatan_satwa:tambah_rekam_medis')
    
    # Ambil data hewan untuk dropdown
    hewan_data = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, nama, spesies, status_kesehatan
                FROM 
                    SIZOPI.HEWAN
                ORDER BY 
                    nama
            """)
            
            for row in cursor.fetchall():
                hewan_data.append({
                    'id': row[0],
                    'nama': row[1],
                    'spesies': row[2],
                    'status_kesehatan': row[3],
                })
    except Exception as e:
        pass
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'hewan_data': hewan_data,
        'today': datetime.now().strftime('%Y-%m-%d')
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/tambah.html', context)

def edit_rekam_medis(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    try:
        # Format ID: id_hewan_tanggal_pemeriksaan
        id_parts = id.split('_')
        if len(id_parts) < 2:
            raise Http404("Rekam medis tidak ditemukan")
        
        id_hewan = id_parts[0]
        tanggal_pemeriksaan = '_'.join(id_parts[1:])
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    cm.tanggal_pemeriksaan,
                    cm.status_kesehatan,
                    cm.diagnosis,
                    cm.pengobatan,
                    cm.catatan_tindak_lanjut
                FROM 
                    SIZOPI.CATATAN_MEDIS cm
                    JOIN SIZOPI.HEWAN h ON cm.id_hewan = h.id
                WHERE 
                    cm.id_hewan = %s AND cm.tanggal_pemeriksaan = %s
            """, [id_hewan, tanggal_pemeriksaan])
            
            result = cursor.fetchone()
            if not result:
                raise Http404("Rekam medis tidak ditemukan")
            
            rekam_medis = {
                'id_hewan': result[0],
                'nama_hewan': result[1],
                'spesies': result[2],
                'tanggal_pemeriksaan': result[3],
                'status_kesehatan': result[4],
                'diagnosis': result[5],
                'pengobatan': result[6],
                'catatan_tindak_lanjut': result[7],
            }
    
    except Exception as e:
        return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    if request.method == 'POST':
        try:
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut')
            diagnosis = request.POST.get('diagnosis')
            pengobatan = request.POST.get('pengobatan')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.CATATAN_MEDIS
                    SET catatan_tindak_lanjut = %s,
                        diagnosis = %s,
                        pengobatan = %s
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [
                    catatan_tindak_lanjut,
                    diagnosis,
                    pengobatan,
                    id_hewan, 
                    tanggal_pemeriksaan
                ])
            
            return redirect('kesehatan_perawatan_satwa:rekam_medis')
            
        except Exception as e:
            pass
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'rekam_medis': rekam_medis,
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/edit.html', context)

def hapus_rekam_medis(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    try:
        # Format ID: id_hewan_tanggal_pemeriksaan
        id_parts = id.split('_')
        if len(id_parts) < 2:
            raise Http404("Rekam medis tidak ditemukan")
        
        id_hewan = id_parts[0]
        tanggal_pemeriksaan = '_'.join(id_parts[1:])
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    cm.tanggal_pemeriksaan,
                    cm.status_kesehatan,
                    cm.diagnosis,
                    cm.pengobatan,
                    cm.catatan_tindak_lanjut
                FROM 
                    SIZOPI.CATATAN_MEDIS cm
                    JOIN SIZOPI.HEWAN h ON cm.id_hewan = h.id
                WHERE 
                    cm.id_hewan = %s AND cm.tanggal_pemeriksaan = %s
            """, [id_hewan, tanggal_pemeriksaan])
            
            result = cursor.fetchone()
            if not result:
                raise Http404("Rekam medis tidak ditemukan")
            
            rekam_medis = {
                'id_hewan': result[0],
                'nama_hewan': result[1],
                'spesies': result[2],
                'tanggal_pemeriksaan': result[3],
                'status_kesehatan': result[4],
                'diagnosis': result[5],
                'pengobatan': result[6],
                'catatan_tindak_lanjut': result[7],
            }
    
        if request.method == 'POST':
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM SIZOPI.CATATAN_MEDIS
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])
            
            return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    except Exception as e:
        return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'rekam_medis': rekam_medis,
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/hapus.html', context)

# ===== JADWAL PEMERIKSAAN =====

def jadwal_pemeriksaan(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                jpk.id_hewan,
                h.nama,
                h.spesies,
                jpk.freq_pemeriksaan_rutin,
                jpk.tgl_pemeriksaan_selanjutnya,
                h.status_kesehatan
            FROM 
                SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN jpk
                JOIN SIZOPI.HEWAN h ON jpk.id_hewan = h.id
            ORDER BY 
                jpk.tgl_pemeriksaan_selanjutnya
        """)
        
        jadwal_pemeriksaan_data = []
        for row in cursor.fetchall():
            jadwal_pemeriksaan_data.append({
                'id_hewan': row[0],
                'nama_hewan': row[1],
                'spesies': row[2],
                'freq_pemeriksaan_rutin': row[3],
                'tgl_pemeriksaan_selanjutnya': row[4],
                'status_kesehatan': row[5],
            })

    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'jadwal_pemeriksaan_data': jadwal_pemeriksaan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/index.html', context)

def tambah_jadwal_pemeriksaan(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    if request.method == 'POST':
        try:
            id_hewan = request.POST.get('id_hewan')
            tgl_pemeriksaan_selanjutnya = request.POST.get('tgl_pemeriksaan_selanjutnya')
            freq_pemeriksaan_rutin = request.POST.get('freq_pemeriksaan_rutin')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 1
                    FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                    WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """, [id_hewan, tgl_pemeriksaan_selanjutnya])
                
                if cursor.fetchone():
                    return redirect('kesehatan_perawatan_satwa:tambah_jadwal_pemeriksaan')
                
                # Tambahkan jadwal baru
                cursor.execute("""
                    INSERT INTO SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                    (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                    VALUES (%s, %s, %s)
                """, [id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin])
            
            return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
            
        except Exception as e:
            return redirect('kesehatan_perawatan_satwa:tambah_jadwal_pemeriksaan')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, nama, spesies, status_kesehatan
            FROM 
                SIZOPI.HEWAN
            ORDER BY 
                nama
        """)
        
        hewan_data = []
        for row in cursor.fetchall():
            hewan_data.append({
                'id': row[0],
                'nama': row[1],
                'spesies': row[2],
                'status_kesehatan': row[3],
            })
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'hewan_data': hewan_data,
        'default_date': (datetime.now()).strftime('%Y-%m-%d')
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/tambah.html', context)

# ===== PEMBERIAN PAKAN (hanya stub functions untuk kompabilitas) =====

def pemberian_pakan(request):
    if 'user_role' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/index.html')

def tambah_pemberian_pakan(request):
    if 'user_role' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/tambah.html')

def edit_pemberian_pakan(request, id):
    if 'user_role' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/edit.html')

def hapus_pemberian_pakan(request, id):
    if 'user_role' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/hapus.html')

def riwayat_pakan(request):
    if 'user_role' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/riwayat.html')

def beri_pakan(request, id):
    if 'user_role' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    return redirect('kesehatan_perawatan_satwa:pemberian_pakan')