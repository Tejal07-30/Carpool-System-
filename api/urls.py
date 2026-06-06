from django.urls import path
from . import views

urlpatterns = [
    path('updatelocation/', views.updatelocation, name='api_updatelocation'),
    path('findtrips/', views.findtrips, name='api_findtrips'),
    path('driverrequests/', views.driverrequests, name='api_driverrequests'),
    path('createoffer/', views.createoffer, name='api_createoffer'),
    path('acceptoffer/', views.acceptoffer, name='api_acceptoffer'),
    path('cancelrequest/', views.cancelrequest, name='api_cancelrequest'),
    path('canceltrip/', views.canceltrip, name='api_canceltrip'),
    path('drivertrips/', views.drivertrips, name='api_drivertrips'),
    path('addmoney/', views.addmoney, name='api_addmoney'),
    path('mywallet/', views.mywallet, name='api_mywallet'),
    path('mytransactions/', views.mytransactions, name='api_mytransactions'),
    path('myrequests/', views.myrequests, name='api_myrequests'),
    path('completetrip/', views.completetrip, name='api_completetrip'),
]
