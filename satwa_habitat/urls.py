from django.urls import path
from . import views

urlpatterns = [
    path('hewan/', views.hewan_list, name='hewan_list'),
    path('hewan/tambah/', views.hewan_create, name='hewan_create'),
    path('hewan/edit/<uuid:pk>/', views.hewan_update, name='hewan_update'),
    path('hewan/hapus/<uuid:pk>/', views.hewan_delete, name='hewan_delete'),
    path('habitat/', views.habitat_list, name='habitat_list'),
    path('habitat/tambah/', views.habitat_create, name='habitat_create'),
    path('habitat/edit/<str:pk>/', views.habitat_update, name='habitat_update'),
    path('habitat/hapus/<str:pk>/', views.habitat_delete, name='habitat_delete'),
    path('habitat/detail/<str:pk>/', views.habitat_detail, name='habitat_detail'),
]
