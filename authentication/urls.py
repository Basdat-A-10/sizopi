from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'), 
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
<<<<<<< HEAD
    path('role/', views.role_selection, name='role'),
    path('gateway/', views.gateway_view, name='gateway'),

=======
    path('gateway/', views.gateway_view, name='gateway'),
>>>>>>> 7d7687d2405124acd4641ad367fae5a9b5f29c1f
]