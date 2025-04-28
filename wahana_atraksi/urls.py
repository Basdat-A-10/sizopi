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
]