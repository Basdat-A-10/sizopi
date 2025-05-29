from django.urls import path
from . import views

urlpatterns = [
    # URL utama - auto redirect berdasarkan role
    path('', views.daftar_wahana_dan_atraksi, name='daftar_wahana_dan_atraksi'),
    
    # Halaman khusus pengunjung
    path('pengunjung/', views.pengunjung_reservasi, name='pengunjung_reservasi'),
    
    # ===== WAHANA MANAGEMENT (Admin Only) =====
    path('wahana/tambah/', views.tambah_wahana, name='tambah_wahana'),
    path('wahana/edit/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
    path('wahana/delete/<str:nama_wahana>/', views.delete_wahana, name='delete_wahana'),
    
    # ===== ATRAKSI MANAGEMENT (Admin Only) =====
    path('atraksi/tambah/', views.tambah_atraksi, name='tambah_atraksi'),
    path('atraksi/edit/<str:nama_atraksi>/', views.edit_atraksi, name='edit_atraksi'),
    path('atraksi/delete/<str:nama_atraksi>/', views.delete_atraksi, name='delete_atraksi'),
    
    # ===== RESERVASI PENGUNJUNG =====
    # Form reservasi (tetap pakai nama asli fasilitas)
    path('reservasi/atraksi/<str:nama_atraksi>/', views.tampil_form_reservasi, name='tampil_form_reservasi'),
    path('reservasi/wahana/<str:nama_wahana>/', views.tampil_form_reservasi_wahana, name='tampil_form_reservasi_wahana'),
    
    # Proses buat reservasi
    path('reservasi/buat/', views.buat_reservasi, name='buat_reservasi'),
    path('reservasi/buat-wahana/', views.buat_reservasi_wahana, name='buat_reservasi_wahana'),
    
    # ===== FIXED: Detail dan edit reservasi - GANTI nama_atraksi dengan nama_fasilitas =====
    path('reservasi/detail/<str:username>/<str:nama_fasilitas>/<str:tanggal_kunjungan>/', 
         views.detail_reservasi, name='detail_reservasi'),
    path('reservasi/edit/form/<str:username>/<str:nama_fasilitas>/<str:tanggal_kunjungan>/', 
         views.tampil_form_edit_reservasi, name='tampil_form_edit_reservasi'),
    path('reservasi/edit/<str:username>/<str:nama_fasilitas>/<str:tanggal_kunjungan>/', 
         views.edit_reservasi, name='edit_reservasi'),
    path('reservasi/batalkan/<str:username>/<str:nama_fasilitas>/<str:tanggal_kunjungan>/', 
         views.batalkan_reservasi, name='batalkan_reservasi'),
    
    # ===== ADMIN RESERVASI MANAGEMENT - FIXED =====
    path('admin/reservasi/edit/<str:username>/<str:nama_fasilitas>/<str:tanggal_kunjungan>/', 
         views.admin_edit_reservasi, name='admin_edit_reservasi'),
    path('admin/reservasi/batalkan/<str:username>/<str:nama_fasilitas>/<str:tanggal_kunjungan>/', 
         views.admin_batalkan_reservasi, name='admin_batalkan_reservasi'),
    
    # ===== BACKWARD COMPATIBILITY (OPTIONAL) =====
    # URL lama yang masih menggunakan nama_atraksi akan di-redirect ke yang baru
    path('reservasi/detail-old/<str:username>/<str:nama_atraksi>/<str:tanggal_kunjungan>/', 
         views.redirect_old_detail_reservasi, name='detail_reservasi_old'),
    path('reservasi/edit-old/<str:username>/<str:nama_atraksi>/<str:tanggal_kunjungan>/', 
         views.redirect_old_edit_reservasi, name='edit_reservasi_old'),
]