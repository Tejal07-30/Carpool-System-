from django.urls import path
from .views import driverdashboard

urlpatterns = [
    path('driverdashboard/', driverdashboard, name='driverdashboard'),
]