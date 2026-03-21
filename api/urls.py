from django.urls import path
from .views import updatelocation, findtrips, createoffer, acceptoffer, cancelrequest, driverrequests, driveroffers, canceltrip, drivertrips, addmoney, createrequest, myrequests
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
]