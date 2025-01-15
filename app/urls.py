from . import views
from django.urls import path
from django.contrib.auth.views import LoginView

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),

    path('signup/', views.signup, name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path("api/get_sas_token/", views.get_sas_url, name="get_sas_token"),
    path("upload_schedule/", views.upload_schedule, name="upload_schedule"),

    path("upload_status/<int:status_id>/", views.upload_status, name="upload_status"),

]