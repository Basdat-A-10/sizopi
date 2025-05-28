from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.db import connection
from django.contrib import messages
from datetime import datetime
import json
from .utils import capture_trigger_messages

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
    
    # data hewan untuk dropdown modal tambah
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
        'rekam_medis_data': rekam_medis_data,
        'hewan_data': hewan_data,
        'today': datetime.now().strftime('%Y-%m-%d')
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/index.html', context)

def tambah_rekam_medis(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    if request.method == 'POST':
        username_dh = request.COOKIES.get('user_id')
        
        try:
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
            status_kesehatan = request.POST.get('status_kesehatan')
            diagnosis = request.POST.get('diagnosis')
            pengobatan = request.POST.get('pengobatan')
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 1
                    FROM SIZOPI.CATATAN_MEDIS
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])
                
                if cursor.fetchone():
                    messages.error(request, "Rekam medis untuk tanggal tersebut sudah ada")
                    return redirect('kesehatan_perawatan_satwa:rekam_medis')
                
                cursor.execute("""
                    SELECT nama FROM SIZOPI.HEWAN WHERE id = %s
                """, [id_hewan])
                
                nama_hewan = cursor.fetchone()[0] if cursor.rowcount > 0 else "Hewan"
                
                cursor.execute("""
                    INSERT INTO SIZOPI.CATATAN_MEDIS
                    (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_hewan
                """, [id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut])
                
                trigger_messages = capture_trigger_messages()
                
                if trigger_messages:
                    for msg in trigger_messages:
                        print(f"DEBUG - Trigger message captured: {repr(msg)}")
                
                if status_kesehatan == 'Sakit':
                    if trigger_messages:
                        for msg in trigger_messages:
                            messages.success(request, msg)
                    else:
                        messages.success(request, f"Jadwal pemeriksaan hewan \"{nama_hewan}\" telah diperbarui karena status kesehatan \"Sakit\".")
                else:
                    if trigger_messages:
                        for msg in trigger_messages:
                            messages.success(request, msg)
                    messages.success(request, f"Rekam medis untuk {nama_hewan} berhasil ditambahkan")
                
                return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    # Jika bukan POST, redirect ke halaman rekam medis
    return redirect('kesehatan_perawatan_satwa:rekam_medis')

def edit_rekam_medis(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    print(f"ID yang diterima di edit: {id}")  
    
    try:
        # Format ID: id_hewan_tanggal_pemeriksaan
        id_parts = id.split('_')
        if len(id_parts) < 2:
            print(f"ID tidak valid di edit: {id}, parts: {id_parts}")
            raise Http404("Rekam medis tidak ditemukan")
        
        id_hewan = id_parts[0]
        tanggal_pemeriksaan = '-'.join(id_parts[1:4])
        
        print(f"ID Hewan di edit: {id_hewan}, Tanggal: {tanggal_pemeriksaan}")
        
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
                print(f"Data tidak ditemukan di edit untuk ID: {id_hewan}, Tanggal: {tanggal_pemeriksaan}")
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
        print(f"Error pada edit_rekam_medis: {str(e)}")
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
            print(f"Error saat update: {str(e)}")
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
            print(f"ID tidak valid: {id}, parts: {id_parts}")
            raise Http404("Rekam medis tidak ditemukan")
        
        id_hewan = id_parts[0]
        tanggal_pemeriksaan = '-'.join(id_parts[1:4])  
        
        print(f"ID Hewan: {id_hewan}, Tanggal: {tanggal_pemeriksaan}")
        
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
                print(f"Data tidak ditemukan untuk ID: {id_hewan}, Tanggal: {tanggal_pemeriksaan}")
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
                # Get animal name before deletion for message
                cursor.execute("""
                    SELECT h.nama FROM SIZOPI.HEWAN h
                    JOIN SIZOPI.CATATAN_MEDIS cm ON h.id = cm.id_hewan
                    WHERE cm.id_hewan = %s AND cm.tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])
                
                result = cursor.fetchone()
                nama_hewan = result[0] if result else "Hewan"
                
                # Delete medical record (this will trigger the cleanup)
                cursor.execute("""
                    DELETE FROM SIZOPI.CATATAN_MEDIS
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])
                
                # Capture trigger messages
                trigger_messages = capture_trigger_messages()
                if trigger_messages:
                    for msg in trigger_messages:
                        messages.success(request, msg)
                else:
                    messages.success(request, f"Rekam medis untuk {nama_hewan} berhasil dihapus")
            
            return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    except Exception as e:
        print(f"Error pada hapus_rekam_medis: {str(e)}")
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

    # data hewan untuk dropdown filter dan modal tambah
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
        'jadwal_pemeriksaan_data': jadwal_pemeriksaan_data,
        'hewan_data': hewan_data,
        'default_date': datetime.now().strftime('%Y-%m-%d')
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/index.html', context)

def tambah_jadwal_pemeriksaan(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    if request.method == 'POST':
        try:
            id_hewan = request.POST.get('id_hewan')
            tgl_pemeriksaan_selanjutnya = request.POST.get('tgl_pemeriksaan_selanjutnya')
            
            filter_hewan = request.GET.get('hewan') or id_hewan
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 1
                    FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                    WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """, [id_hewan, tgl_pemeriksaan_selanjutnya])
                
                if cursor.fetchone():
                    messages.warning(request, "Jadwal pada tanggal tersebut sudah ada")
                else:
                    cursor.execute("""
                        SELECT nama FROM SIZOPI.HEWAN WHERE id = %s
                    """, [id_hewan])
                    
                    nama_hewan = cursor.fetchone()[0] if cursor.rowcount > 0 else "Hewan"
                    
                    # Insert jadwal baru (frekuensi akan menggunakan default dari SQL)
                    cursor.execute("""
                        INSERT INTO SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                        (id_hewan, tgl_pemeriksaan_selanjutnya)
                        VALUES (%s, %s)
                    """, [id_hewan, tgl_pemeriksaan_selanjutnya])
                    
                    # Tangkap pesan trigger
                    trigger_messages = capture_trigger_messages()
                    for msg in trigger_messages:
                        messages.success(request, msg)
                    
                    if not trigger_messages:
                        messages.success(request, f"Jadwal pemeriksaan untuk {nama_hewan} berhasil ditambahkan")
            
            if filter_hewan:
                return redirect(f'/kesehatan-perawatan/jadwal-pemeriksaan/?hewan={filter_hewan}')
            else:
                return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
            
        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')

def edit_jadwal_pemeriksaan(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    jpk.freq_pemeriksaan_rutin,
                    jpk.tgl_pemeriksaan_selanjutnya,
                    h.status_kesehatan
                FROM 
                    SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN jpk
                    JOIN SIZOPI.HEWAN h ON jpk.id_hewan = h.id
                WHERE 
                    jpk.id_hewan = %s
            """, [id])
            
            result = cursor.fetchone()
            if not result:
                raise Http404("Jadwal pemeriksaan tidak ditemukan")
            
            jadwal = {
                'id_hewan': result[0],
                'nama_hewan': result[1],
                'spesies': result[2],
                'freq_pemeriksaan_rutin': result[3],
                'tgl_pemeriksaan_selanjutnya': result[4],
                'status_kesehatan': result[5],
            }
    
        if request.method == 'POST':
            tgl_pemeriksaan_selanjutnya = request.POST.get('tgl_pemeriksaan_selanjutnya')
            
            filter_hewan = request.GET.get('hewan') or id
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                    SET tgl_pemeriksaan_selanjutnya = %s
                    WHERE id_hewan = %s
                """, [tgl_pemeriksaan_selanjutnya, id])
                
                messages.success(request, f"Jadwal pemeriksaan berhasil diperbarui")
        
            if filter_hewan:
                return redirect(f'/kesehatan-perawatan/jadwal-pemeriksaan/?hewan={filter_hewan}')
            else:
                return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'jadwal': jadwal,
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/edit.html', context)

def edit_frekuensi_pemeriksaan(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    jpk.freq_pemeriksaan_rutin,
                    h.status_kesehatan
                FROM 
                    SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN jpk
                    JOIN SIZOPI.HEWAN h ON jpk.id_hewan = h.id
                WHERE 
                    jpk.id_hewan = %s
            """, [id])
            
            result = cursor.fetchone()
            if not result:
                raise Http404("Jadwal pemeriksaan tidak ditemukan")
            
            jadwal = {
                'id_hewan': result[0],
                'nama_hewan': result[1],
                'spesies': result[2],
                'freq_pemeriksaan_rutin': result[3],
                'status_kesehatan': result[4],
            }
    
        if request.method == 'POST':
            freq_pemeriksaan_rutin = request.POST.get('freq_pemeriksaan_rutin')
            
            filter_hewan = request.GET.get('hewan') or id
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                    SET freq_pemeriksaan_rutin = %s
                    WHERE id_hewan = %s
                """, [freq_pemeriksaan_rutin, id])
                
                # Tangkap pesan trigger
                trigger_messages = capture_trigger_messages()
                for msg in trigger_messages:
                    messages.success(request, msg)
                
                if not trigger_messages:
                    messages.success(request, f"Frekuensi pemeriksaan berhasil diperbarui")
        
        if request.method == 'POST':
            filter_hewan = request.GET.get('hewan') or id
            if filter_hewan:
                return redirect(f'/kesehatan-perawatan/jadwal-pemeriksaan/?hewan={filter_hewan}')
            else:
                return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'jadwal': jadwal,
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/edit_frekuensi.html', context)

def hapus_jadwal_pemeriksaan(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'dokter_hewan':
        return redirect('login')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    jpk.freq_pemeriksaan_rutin,
                    jpk.tgl_pemeriksaan_selanjutnya,
                    h.status_kesehatan
                FROM 
                    SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN jpk
                    JOIN SIZOPI.HEWAN h ON jpk.id_hewan = h.id
                WHERE 
                    jpk.id_hewan = %s
            """, [id])
            
            result = cursor.fetchone()
            if not result:
                raise Http404("Jadwal pemeriksaan tidak ditemukan")
            
            jadwal = {
                'id_hewan': result[0],
                'nama_hewan': result[1],
                'spesies': result[2],
                'freq_pemeriksaan_rutin': result[3],
                'tgl_pemeriksaan_selanjutnya': result[4],
                'status_kesehatan': result[5],
            }
    
        if request.method == 'POST':
            filter_hewan = request.GET.get('hewan') or id
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM SIZOPI.JADWAL_PEMERIKSAAN_KESEHATAN
                    WHERE id_hewan = %s
                """, [id])
            
            if filter_hewan:
                return redirect(f'/kesehatan-perawatan/jadwal-pemeriksaan/?hewan={filter_hewan}')
            else:
                return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'jadwal': jadwal,
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/hapus.html', context)

# ===== PEMBERIAN PAKAN =====

def pemberian_pakan(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    
    username_jh = request.COOKIES.get('user_id')
    pakan_data = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id_hewan,
                    h.nama,
                    h.spesies,
                    p.jenis,
                    p.jumlah,
                    p.jadwal,
                    p.status
                FROM 
                    SIZOPI.PAKAN p
                    JOIN SIZOPI.HEWAN h ON p.id_hewan = h.id
                ORDER BY 
                    p.jadwal
            """)
            
            for row in cursor.fetchall():
                pakan_data.append({
                    'id_hewan': row[0],
                    'nama_hewan': row[1],
                    'spesies': row[2],
                    'jenis_pakan': row[3],
                    'jumlah_pakan': row[4],
                    'jadwal': row[5],
                    'status': row[6],
                    'jadwal_str': row[5].strftime('%Y-%m-%d-%H-%M-%S') if row[5] else ''
                })
    except Exception as e:
        print(f"Error: {str(e)}")
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'pakan_data': pakan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/index.html', context)

def tambah_pemberian_pakan(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    
    username_jh = request.COOKIES.get('user_id')
    
    if request.method == 'POST':
        try:
            id_hewan = request.POST.get('id_hewan')
            jenis_pakan = request.POST.get('jenis_pakan')
            jumlah_pakan = request.POST.get('jumlah_pakan')
            jadwal = request.POST.get('jadwal')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO SIZOPI.PAKAN
                    (id_hewan, jadwal, jenis, jumlah, status)
                    VALUES (%s, %s, %s, %s, 'Terjadwal')
                """, [id_hewan, jadwal, jenis_pakan, jumlah_pakan])
                
                print(f"Jadwal pemberian pakan berhasil ditambahkan: id_hewan={id_hewan}, jadwal={jadwal}")
            
            return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
            
        except Exception as e:
            print(f"Error saat tambah pemberian pakan: {str(e)}")
    
    # Data hewan untuk dropdown
    hewan_data = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, nama, spesies
                FROM 
                    SIZOPI.HEWAN
                ORDER BY 
                    nama
            """)
            
            for row in cursor.fetchall():
                hewan_data.append({
                    'id': row[0],
                    'nama': row[1],
                    'spesies': row[2]
                })
    except Exception as e:
        print(f"Error saat mengambil data hewan: {str(e)}")
    
    from datetime import datetime, timedelta
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'hewan_data': hewan_data,
        'default_datetime': (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/tambah.html', context)

def edit_pemberian_pakan(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    
    username_jh = request.COOKIES.get('user_id')
    
    try:
        if id.startswith('20'):
            jadwal_timestamp = id
            jadwal = datetime.strptime(jadwal_timestamp, '%Y-%m-%d-%H-%M-%S')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.id_hewan, h.nama, h.spesies, p.jenis, p.jumlah, p.jadwal, p.status
                    FROM SIZOPI.PAKAN p
                    JOIN SIZOPI.HEWAN h ON p.id_hewan = h.id
                    WHERE p.jadwal = %s
                """, [jadwal])
                
                result = cursor.fetchone()
                if not result:
                    print(f"Error: Data tidak ditemukan untuk jadwal: {jadwal}")
                    raise Http404("Data pemberian pakan tidak ditemukan")
                
                id_hewan = result[0]
                
                pakan = {
                    'id_hewan': result[0],
                    'nama_hewan': result[1],
                    'spesies': result[2],
                    'jenis_pakan': result[3],
                    'jumlah_pakan': result[4],
                    'jadwal': result[5],
                    'status': result[6],
                    'jadwal_str': result[5].strftime('%Y-%m-%dT%H:%M') if result[5] else ''
                }
        else:
            # Format ID: id_hewan_jadwal_timestamp
            id_parts = id.split('_')
            if len(id_parts) < 2:
                print(f"Error: ID tidak valid: {id}")
                raise Http404("Data pemberian pakan tidak ditemukan")
            
            id_hewan = id_parts[0]
            jadwal_timestamp = '_'.join(id_parts[1:])
            
            jadwal = datetime.strptime(jadwal_timestamp, '%Y-%m-%d-%H-%M-%S')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.id_hewan,
                        h.nama,
                        h.spesies,
                        p.jenis,
                        p.jumlah,
                        p.jadwal,
                        p.status
                    FROM 
                        SIZOPI.PAKAN p
                        JOIN SIZOPI.HEWAN h ON p.id_hewan = h.id
                    WHERE 
                        p.id_hewan = %s AND p.jadwal = %s
                """, [id_hewan, jadwal])
                
                result = cursor.fetchone()
                if not result:
                    print(f"Error: Data tidak ditemukan untuk ID: {id_hewan}, Jadwal: {jadwal}")
                    raise Http404("Data pemberian pakan tidak ditemukan")
                
                pakan = {
                    'id_hewan': result[0],
                    'nama_hewan': result[1],
                    'spesies': result[2],
                    'jenis_pakan': result[3],
                    'jumlah_pakan': result[4],
                    'jadwal': result[5],
                    'status': result[6],
                    'jadwal_str': result[5].strftime('%Y-%m-%dT%H:%M') if result[5] else ''
                }
    
        if request.method == 'POST':
            jenis_pakan_baru = request.POST.get('jenis_pakan')
            jumlah_pakan_baru = request.POST.get('jumlah_pakan')
            jadwal_baru = request.POST.get('jadwal')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.PAKAN
                    SET jenis = %s, jumlah = %s, jadwal = %s
                    WHERE id_hewan = %s AND jadwal = %s
                """, [
                    jenis_pakan_baru,
                    jumlah_pakan_baru,
                    jadwal_baru,
                    id_hewan,
                    jadwal
                ])
                
                if pakan['status'] == 'Selesai Diberikan':
                    cursor.execute("""
                        UPDATE SIZOPI.MEMBERI
                        SET jadwal = %s
                        WHERE id_hewan = %s AND jadwal = %s
                    """, [jadwal_baru, id_hewan, jadwal])
            
            return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
            
    except Exception as e:
        print(f"Error saat edit pemberian pakan: {str(e)}")
        return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'pakan': pakan,
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/edit.html', context)

def hapus_pemberian_pakan(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    
    username_jh = request.COOKIES.get('user_id')
    
    try:
        if id.startswith('20'):
            jadwal_timestamp = id
            jadwal = datetime.strptime(jadwal_timestamp, '%Y-%m-%d-%H-%M-%S')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.id_hewan, h.nama, h.spesies, p.jenis, p.jumlah, p.jadwal, p.status
                    FROM SIZOPI.PAKAN p
                    JOIN SIZOPI.HEWAN h ON p.id_hewan = h.id
                    WHERE p.jadwal = %s
                """, [jadwal])
                
                result = cursor.fetchone()
                if not result:
                    print(f"Error: Data tidak ditemukan untuk jadwal: {jadwal}")
                    raise Http404("Data pemberian pakan tidak ditemukan")
                
                id_hewan = result[0]
                
                pakan = {
                    'id_hewan': result[0],
                    'nama_hewan': result[1],
                    'spesies': result[2],
                    'jenis_pakan': result[3],
                    'jumlah_pakan': result[4],
                    'jadwal': result[5],
                    'status': result[6],
                    'jadwal_str': result[5].strftime('%d %b %Y %H:%M') if result[5] else ''
                }
        else:
            # Format ID: id_hewan_jadwal_timestamp
            id_parts = id.split('_')
            if len(id_parts) < 2:
                print(f"Error: ID tidak valid: {id}")
                raise Http404("Data pemberian pakan tidak ditemukan")
            
            id_hewan = id_parts[0]
            jadwal_timestamp = '_'.join(id_parts[1:])
            
            jadwal = datetime.strptime(jadwal_timestamp, '%Y-%m-%d-%H-%M-%S')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.id_hewan,
                        h.nama,
                        h.spesies,
                        p.jenis,
                        p.jumlah,
                        p.jadwal,
                        p.status
                    FROM 
                        SIZOPI.PAKAN p
                        JOIN SIZOPI.HEWAN h ON p.id_hewan = h.id
                    WHERE 
                        p.id_hewan = %s AND p.jadwal = %s
                """, [id_hewan, jadwal])
                
                result = cursor.fetchone()
                if not result:
                    print(f"Error: Data tidak ditemukan untuk ID: {id_hewan}, Jadwal: {jadwal}")
                    raise Http404("Data pemberian pakan tidak ditemukan")
                
                pakan = {
                    'id_hewan': result[0],
                    'nama_hewan': result[1],
                    'spesies': result[2],
                    'jenis_pakan': result[3],
                    'jumlah_pakan': result[4],
                    'jadwal': result[5],
                    'status': result[6],
                    'jadwal_str': result[5].strftime('%d %b %Y %H:%M') if result[5] else ''
                }
    
        if request.method == 'POST':
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM SIZOPI.MEMBERI
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
                
                # Hapus dari tabel PAKAN
                cursor.execute("""
                    DELETE FROM SIZOPI.PAKAN
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
            
            return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
            
    except Exception as e:
        print(f"Error saat hapus pemberian pakan: {str(e)}")
        return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'pakan': pakan,
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/hapus.html', context)

def beri_pakan(request, id):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    
    username_jh = request.COOKIES.get('user_id')
    
    try:
        if id.startswith('20'):  
            jadwal_timestamp = id
            jadwal = datetime.strptime(jadwal_timestamp, '%Y-%m-%d-%H-%M-%S')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id_hewan, status FROM SIZOPI.PAKAN
                    WHERE jadwal = %s
                """, [jadwal])
                
                result = cursor.fetchone()
                if not result:
                    print(f"Error: Tidak ditemukan jadwal pakan untuk {jadwal}")
                    return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
                
                id_hewan, status = result
                
                if status != 'Terjadwal':
                    print(f"Error: Status pakan sudah {status}, bukan Terjadwal")
                    return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
                
                # Update status di tabel PAKAN
                cursor.execute("""
                    UPDATE SIZOPI.PAKAN
                    SET status = 'Selesai Diberikan'
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
                
                cursor.execute("""
                    SELECT 1 FROM SIZOPI.MEMBERI
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
                
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE SIZOPI.MEMBERI
                        SET username_jh = %s
                        WHERE id_hewan = %s AND jadwal = %s
                    """, [username_jh, id_hewan, jadwal])
                    print(f"Data MEMBERI diupdate: id_hewan={id_hewan}, jadwal={jadwal}")
                else:
                    cursor.execute("""
                        INSERT INTO SIZOPI.MEMBERI (id_hewan, jadwal, username_jh)
                        VALUES (%s, %s, %s)
                    """, [id_hewan, jadwal, username_jh])
                    print(f"Data MEMBERI baru dibuat: id_hewan={id_hewan}, jadwal={jadwal}")
        else:
            print(f"Format ID tidak didukung: {id}")
            
    except Exception as e:
        print(f"Error saat beri pakan: {str(e)}")
    
    return redirect('kesehatan_perawatan_satwa:pemberian_pakan')

def riwayat_pakan(request):
    if 'user_id' not in request.COOKIES or request.COOKIES.get('user_role') != 'penjaga_hewan':
        return redirect('login')
    
    username_jh = request.COOKIES.get('user_id')
    riwayat_pakan_data = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.nama,
                    h.spesies,
                    h.asal_hewan,
                    h.tanggal_lahir,
                    h.nama_habitat,
                    h.status_kesehatan,
                    p.jenis,
                    p.jumlah,
                    p.jadwal,
                    m.username_jh
                FROM 
                    SIZOPI.MEMBERI m
                JOIN SIZOPI.HEWAN h ON m.id_hewan = h.id
                JOIN SIZOPI.PAKAN p ON m.id_hewan = p.id_hewan AND m.jadwal = p.jadwal
                WHERE 
                    m.username_jh = %s AND p.status = 'Selesai Diberikan'
                ORDER BY 
                    p.jadwal DESC
            """, [username_jh])
            
            for row in cursor.fetchall():
                jadwal_obj = row[9]
                jadwal_formatted = jadwal_obj.strftime('%d %b %Y %H:%M') if jadwal_obj else ''
                
                riwayat_pakan_data.append({
                    'id_hewan': row[0],
                    'nama_hewan': row[1],
                    'spesies': row[2],
                    'asal_hewan': row[3],
                    'tanggal_lahir': row[4].strftime('%d %b %Y') if row[4] else '',
                    'habitat': row[5] if row[5] else 'Tidak ada',
                    'status_kesehatan': row[6],
                    'jenis_pakan': row[7],
                    'jumlah_pakan': row[8],
                    'jadwal': jadwal_formatted,
                    'pemberi': row[10]
                })
                
            print(f"Jumlah data riwayat pakan: {len(riwayat_pakan_data)}")
    except Exception as e:
        print(f"Error saat mengambil riwayat pakan: {str(e)}")
    
    context = {
        'user_id': request.COOKIES.get('user_id'),
        'user_fullname': request.COOKIES.get('user_fullname'),
        'user_role': request.COOKIES.get('user_role'),
        'riwayat_pakan_data': riwayat_pakan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/riwayat.html', context)