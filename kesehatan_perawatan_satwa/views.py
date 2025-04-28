from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
from . import dummy_data

def index(request):
    return render(request, 'kesehatan_perawatan_satwa/index.html')

# ===== REKAM MEDIS =====

def rekam_medis(request):
    context = {
        'rekam_medis_data': dummy_data.rekam_medis_data,
        'hewan_data': dummy_data.hewan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/index.html', context)

def tambah_rekam_medis(request):
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    context = {
        'hewan_data': dummy_data.hewan_data,
        'dokter_hewan': dummy_data.dokter_hewan
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/tambah.html', context)

def edit_rekam_medis(request, id):
    rekam_medis = next((rm for rm in dummy_data.rekam_medis_data if rm['id'] == id), None)
    
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    context = {
        'rekam_medis': rekam_medis
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/edit.html', context)

def hapus_rekam_medis(request, id):
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:rekam_medis')
    
    rekam_medis = next((rm for rm in dummy_data.rekam_medis_data if rm['id'] == id), None)
    
    if rekam_medis and 'tanggal_pemeriksaan' in rekam_medis:
        # Format tanggal sesuai kebutuhan
        tanggal = rekam_medis['tanggal_pemeriksaan']
        # parts = tanggal.split('-')
        # if len(parts) == 3:
        #     rekam_medis['tanggal_pemeriksaan'] = f"{parts[2]} {get_month_name(parts[1])} {parts[0]}"
    
    context = {
        'rekam_medis': rekam_medis
    }
    return render(request, 'kesehatan_perawatan_satwa/rekam_medis/hapus.html', context)

# ===== JADWAL PEMERIKSAAN =====

def jadwal_pemeriksaan(request):
    context = {
        'jadwal_pemeriksaan_data': dummy_data.jadwal_pemeriksaan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/index.html', context)

def tambah_jadwal_pemeriksaan(request):
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:jadwal_pemeriksaan')
    
    context = {
        'hewan_data': dummy_data.hewan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/jadwal_pemeriksaan/tambah.html', context)

# ===== PEMBERIAN PAKAN =====

def pemberian_pakan(request):
    context = {
        'pemberian_pakan_data': dummy_data.pemberian_pakan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/index.html', context)

def tambah_pemberian_pakan(request):
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
    
    context = {
        'hewan_data': dummy_data.hewan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/tambah.html', context)

def edit_pemberian_pakan(request, id):
    pemberian_pakan = next((pp for pp in dummy_data.pemberian_pakan_data if pp['id'] == id), None)
    
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
    
    context = {
        'pemberian_pakan': pemberian_pakan
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/edit.html', context)

def hapus_pemberian_pakan(request, id):
    if request.method == 'POST':
        return redirect('kesehatan_perawatan_satwa:pemberian_pakan')
    
    pemberian_pakan = next((pp for pp in dummy_data.pemberian_pakan_data if pp['id'] == id), None)
    
    context = {
        'pemberian_pakan': pemberian_pakan
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/hapus.html', context)

def riwayat_pakan(request):
    context = {
        'riwayat_pakan_data': dummy_data.riwayat_pakan_data
    }
    return render(request, 'kesehatan_perawatan_satwa/pemberian_pakan/riwayat.html', context)

def beri_pakan(request, id):
    for i, pakan in enumerate(dummy_data.pemberian_pakan_data):
        if pakan['id'] == id:
            dummy_data.pemberian_pakan_data[i]['status'] = "Selesai Diberikan"
            
            hewan = next((h for h in dummy_data.hewan_data if h['id'] == pakan['id_hewan']), None)
            
            if hewan:
                riwayat = {
                    'nama_hewan': pakan['nama_hewan'],
                    'spesies': hewan['spesies'],
                    'asal_hewan': hewan['asal_hewan'],
                    'tanggal_lahir': hewan['tanggal_lahir'],
                    'habitat': hewan['nama_habitat'],
                    'status_kesehatan': hewan['status_kesehatan'],
                    'jenis_pakan': pakan['jenis_pakan'],
                    'jumlah_pakan': pakan['jumlah_pakan'],
                    'jadwal': pakan['jadwal']
                }
                
                if not any(r['nama_hewan'] == riwayat['nama_hewan'] and 
                          r['jadwal'] == riwayat['jadwal'] for r in dummy_data.riwayat_pakan_data):
                    dummy_data.riwayat_pakan_data.append(riwayat)
            
            break
    
    return redirect('kesehatan_perawatan_satwa:pemberian_pakan')