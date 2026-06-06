from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Driver
    path('driver/dashboard/', views.driverdashboard, name='driverdashboard'),
    path('driver/offer/<int:requestid>/', views.offer_ride, name='offerride'),
    path('driver/complete/', views.complete_trip, name='completetrip'),

    # Passenger
    path('passenger/', views.passengerdashboard, name='passengerdashboard'),
    path('passenger/requests/', views.passenger_requests, name='passengerrequests'),
    path('passenger/request/create/', views.create_request, name='createrequest'),
    path('passenger/confirm/', views.confirm_offer, name='confirmoffer'),
    path('passenger/cancel/', views.cancel_request, name='cancelrequest'),

    # Wallet
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/add/', views.add_money, name='addmoney'),
]
