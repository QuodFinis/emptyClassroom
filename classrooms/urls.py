from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('verify_email', views.verify_email, name='verify_email'),
    path('login/', views.login, name='login'),

    path('import-data/', views.import_data, name='import_data'),
]