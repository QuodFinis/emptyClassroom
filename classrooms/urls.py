from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('all-rooms/', views.all_rooms, name='all_rooms'),
    path('colleges/', views.colleges, name='colleges'),
    path('colleges/<str:college_name>/buildings/', views.college_buildings, name='college_buildings'),
    path('colleges/<str:college_name>/buildings/<str:building_name>/', views.building_rooms, name='building_rooms'),
    path('signup/', views.signup, name='signup'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('login/', views.login, name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='forgot_password.html'), name='password_reset'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', auth_views.PasswordResetView.as_view(template_name='change_password.html'), name='password_change'),
    path('import-data/', views.import_data, name='import_data'),
]
