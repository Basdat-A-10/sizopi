from django.urls import path
from . import views

urlpatterns = [
    path('adopters/', views.adopter_list, name='adopter_list'),
    path('adopters/<uuid:id_adopter>/', views.adopter_detail, name='adopter_detail'),
    path('adopters/<uuid:id_adopter>/delete/', views.delete_adopter, name='delete_adopter'),
    path('adoptions/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/delete/', views.delete_adopsi, name='delete_adopsi'),
    path('', views.adopsi_home, name='adopsi_home'),
    path('form-individu/', views.form_individu, name='form_individu'),
    path('form-organisasi/', views.form_organisasi, name='form_organisasi'),
    path('adopter-home/', views.adopter_home, name='adopter_home'),
]
