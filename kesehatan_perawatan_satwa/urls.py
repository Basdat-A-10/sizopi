from django.urls import path
from . import views

app_name = 'kesehatan_perawatan_satwa'

urlpatterns = [
    path('', views.index, name='index'),
]