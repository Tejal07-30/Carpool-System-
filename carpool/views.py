from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from trip.models import Trip
from .models import CarpoolOffer
from .utils import computeoffer
from .views import generateoffersfortrip

def createofferforrequest(trip, carpoolrequest):
    result = computeoffer(
        trip,
        carpoolrequest.pickup,
        carpoolrequest.drop
    )

    if not result:
        return None

    offer = CarpoolOffer.objects.create(
        trip=trip,
        request=carpoolrequest,
        detour=result["detour"],
        fare=result["fare"]
    )

    return offer

def generateoffersfortrip(trip):
    requests = CarpoolRequest.objects.filter(status='pending')

    for req in requests:
        if not isrequestvalid(trip, req.pickup, req.drop):
            continue
        alreadyexists = CarpoolOffer.objects.filter(
            trip=trip,
            request=req
        ).exists()

        if alreadyexists:
            continue
        createofferforrequest(trip, req)
@login_required
def driverdashboard(request):
    trip = Trip.objects.filter(
        driver=request.user,
        status='active'
    ).first()

    offers = []

    if trip:
        generateoffersfortrip(trip)
        offers = CarpoolOffer.objects.filter(trip=trip)

    return render(request, 'driverdashboard.html', {
        'offers': offers,
        'trip': trip
    })