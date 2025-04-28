from django.urls import path
from . import views

app_name = 'kesehatan_perawatan_satwa'

urlpatterns = [
    path('', views.index, name='index'),
    path('rekam-medis/', views.rekam_medis, name='rekam_medis'),
    path('rekam-medis/tambah/', views.tambah_rekam_medis, name='tambah_rekam_medis'),
    path('rekam-medis/edit/<str:id>/', views.edit_rekam_medis, name='edit_rekam_medis'),
    path('rekam-medis/hapus/<str:id>/', views.hapus_rekam_medis, name='hapus_rekam_medis'),
    path('jadwal-pemeriksaan/', views.jadwal_pemeriksaan, name='jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/tambah/', views.tambah_jadwal_pemeriksaan, name='tambah_jadwal_pemeriksaan'),
    path('pemberian-pakan/', views.pemberian_pakan, name='pemberian_pakan'),
    path('pemberian-pakan/tambah/', views.tambah_pemberian_pakan, name='tambah_pemberian_pakan'),
    path('pemberian-pakan/edit/<str:id>/', views.edit_pemberian_pakan, name='edit_pemberian_pakan'),
    path('pemberian-pakan/hapus/<str:id>/', views.hapus_pemberian_pakan, name='hapus_pemberian_pakan'),
    path('pemberian-pakan/beri-pakan/<str:id>/', views.beri_pakan, name='beri_pakan'),
    path('riwayat-pakan/', views.riwayat_pakan, name='riwayat_pakan'),
]