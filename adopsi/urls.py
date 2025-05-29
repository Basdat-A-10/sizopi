from django.urls import path
from . import views

urlpatterns = [
    path('adopters/', views.adopter_list, name='adopter_list'),
    path('adopters/<uuid:id_adopter>/', views.adopter_detail, name='adopter_detail'),
    path('adopters/<uuid:id_adopter>/delete/', views.delete_adopter, name='delete_adopter'),
    path('adoptions/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/delete/', views.delete_adopsi, name='delete_adopsi'),
    path('', views.adopsi_home, name='adopsi_home'),
    path('adopter-home/', views.adopter_home, name='adopter_home'),
    path('adoptions/<uuid:id_hewan>/update-status/', views.update_status_pembayaran, name='update_status_pembayaran'),
    path('adopsi/delete/<uuid:id_hewan>/', views.hentikan_adopsi, name='hentikan_adopsi'),
    path('adopsi/verifikasi/<uuid:id_hewan>/', views.verifikasi_adopter, name='verifikasi_adopter'),
    path('adopsi/submit/individu/', views.submit_adopsi_individu, name='submit_adopsi_individu'),
    path('adopsi/submit/organisasi/', views.submit_adopsi_organisasi, name='submit_adopsi_organisasi'),
    path('adopter-home-user/', views.adopsi_home_adopter, name='adopsi_home_adopter'),
    path('stop-adopsi/<uuid:id_hewan>/', views.hentikan_adopsi, name='hentikan_adopsi'),
    path('adopsi/perpanjang/individu/<uuid:id_hewan>/', views.perpanjang_adopsi_individu, name='perpanjang_adopsi_individu'),
    path('adopsi/perpanjang/organisasi/<uuid:id_hewan>/', views.perpanjang_adopsi_organisasi, name='perpanjang_adopsi_organisasi'),
]
