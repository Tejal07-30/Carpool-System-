from django.urls import path
from .views import *

urlpatterns = [
    path('driverdashboard/', driverdashboard, name='driverdashboard'),

    path('driver/createoffer/', createoffer, name='createoffer'),
    path('driver/complete_trip/', completetripview, name='completetrip'),
    path('passenger/', passengerdashboard, name='passengerdashboard'),
    path('passenger/create/', createrequest, name='createrequest'),
    path('passenger/requests/', passengerrequests, name='passengerrequests'),
    path('passenger/confirmoffer/', confirmoffer, name='confirmoffer'),
    path('passenger/cancel/', cancelrequestview, name='cancelrequest'),
    path('offers/<int:request_id>/', offerride, name='offerride'),
    path('wallet/', walletview, name="wallet"),
    path('wallet/add/', addmoneyview, name="addmoney"),
    path('accept-driver/<int:offerid>/', acceptdriver, name='acceptdriver'),
    path('accept-offer/<int:offerid>/', acceptoffer, name='acceptoffer')
]