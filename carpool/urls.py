from django.urls import path
from .views import driverdashboard, createrequest, passengeroffers, walletview

urlpatterns = [
    path('driverdashboard/', driverdashboard, name='driverdashboard'),
    path('passengerrequest/', createrequest),
    path('passengeroffers/', passengeroffers),
    path('wallet/', walletview),
]