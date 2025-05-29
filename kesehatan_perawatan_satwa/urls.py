from django.urls import path
from . import views

app_name = 'kesehatan_perawatan_satwa'
urlpatterns = [
    path('', views.index, name='index'),
    
    # Rekam Medis
    path('rekam-medis/', views.rekam_medis, name='rekam_medis'),
    path('rekam-medis/tambah/', views.tambah_rekam_medis, name='tambah_rekam_medis'),
    path('rekam-medis/edit/<str:id>/', views.edit_rekam_medis, name='edit_rekam_medis'),
    path('rekam-medis/hapus/<str:id>/', views.hapus_rekam_medis, name='hapus_rekam_medis'),
    
    # Jadwal Pemeriksaan
    path('jadwal-pemeriksaan/', views.jadwal_pemeriksaan, name='jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/tambah/', views.tambah_jadwal_pemeriksaan, name='tambah_jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/edit/<str:id>/', views.edit_jadwal_pemeriksaan, name='edit_jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/edit-frekuensi/<str:id>/', views.edit_frekuensi_pemeriksaan, name='edit_frekuensi_pemeriksaan'),
    path('jadwal-pemeriksaan/hapus/<str:id>/', views.hapus_jadwal_pemeriksaan, name='hapus_jadwal_pemeriksaan'),
    
    # Pemberian Pakan 
    path('pemberian-pakan/', views.pemberian_pakan, name='pemberian_pakan'),
    path('pemberian-pakan/tambah/', views.tambah_pemberian_pakan, name='tambah_pemberian_pakan'),
    path('pemberian-pakan/edit/<str:id>/', views.edit_pemberian_pakan, name='edit_pemberian_pakan'),
    path('pemberian-pakan/hapus/<str:id>/', views.hapus_pemberian_pakan, name='hapus_pemberian_pakan'),
    path('pemberian-pakan/beri-pakan/<str:id>/', views.beri_pakan, name='beri_pakan'),
    path('pemberian-pakan/riwayat/', views.riwayat_pakan, name='riwayat_pakan'),
]