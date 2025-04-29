from django.urls import path
from . import views

urlpatterns = [
    # Main view
    path('', views.daftar_wahana_dan_atraksi, name='daftar_wahana_dan_atraksi'),
    
    # Wahana URLs
    path('wahana/tambah/', views.tambah_wahana, name='tambah_wahana'),
    path('wahana/edit/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
    path('wahana/delete/<str:nama_wahana>/', views.delete_wahana, name='delete_wahana'),
    
    # Atraksi URLs
    path('atraksi/tambah/', views.tambah_atraksi, name='tambah_atraksi'),
    path('atraksi/edit/<str:nama_atraksi>/', views.edit_atraksi, name='edit_atraksi'),
    path('atraksi/delete/<str:nama_atraksi>/', views.delete_atraksi, name='delete_atraksi'),
    
    # Reservasi URLs - Using separate HTML pages
    path('reservasi/form/<str:nama_atraksi>/', views.tampil_form_reservasi, name='tampil_form_reservasi'),
    path('reservasi/buat/', views.buat_reservasi, name='buat_reservasi'),
    path('reservasi/detail/<str:username>/<str:nama_atraksi>/<str:tanggal_kunjungan>/', 
         views.detail_reservasi, name='detail_reservasi'),
    path('reservasi/edit/form/<str:username>/<str:nama_atraksi>/<str:tanggal_kunjungan>/', 
         views.tampil_form_edit_reservasi, name='tampil_form_edit_reservasi'),
    path('reservasi/edit/<str:username>/<str:nama_atraksi>/<str:tanggal_kunjungan>/', 
         views.edit_reservasi, name='edit_reservasi'),
    path('reservasi/batalkan/<str:username>/<str:nama_atraksi>/<str:tanggal_kunjungan>/', 
         views.batalkan_reservasi, name='batalkan_reservasi'),
]