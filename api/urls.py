from django.urls import path
from .views import updatelocation, findtrips, createoffer, acceptoffer, cancelrequest, driverrequests, driveroffers, canceltrip, drivertrips, addmoney, createrequest, myrequests, completetrip, mywallet, mytransactions
urlpatterns = [
    path('updatelocation/', updatelocation),
    path('findtrips/', findtrips),
    path('createoffer/', createoffer),
    path('acceptoffer/', acceptoffer),
    path('cancelrequest/', cancelrequest),
    path('driverrequests/', driverrequests),
    path('driveroffers/', driveroffers),
    path('canceltrip/', canceltrip),
    path('drivertrips/', drivertrips),
    path('addmoney/', addmoney),
    path('createrequest/', createrequest),
    path('myrequests/', myrequests),
    path('completetrip/', completetrip),
    path('mywallet/', mywallet),
    path('mytransactions/', mytransactions),
]