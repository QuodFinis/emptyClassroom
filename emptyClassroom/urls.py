from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('classrooms.urls')),  # Main homepage using classrooms app
]
