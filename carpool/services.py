#newly added functions for correction or linking error(to be removed later).

from .models import CarpoolRequest, CarpoolOffer
from trips.models import Trip
from network.models import Node


def createcarpoolrequest(user, pickup, dropoff):
    request = CarpoolRequest.objects.create(
        user=user,
        pickup=pickup,
        dropoff=dropoff,
        status='pending'
    )
    return request

def getdriveractivetrip(driver):
    return Trip.objects.filter(driver=driver, status='active').first()


def iswithintwonodes(routenodes, node):
    return any(
        abs(routenodes.index(n) - routenodes.index(node)) <= 2
        for n in routenodes if n == node
    )


def getmatchingrequestsfordriver(driver):
    trip = getdriveractivetrip(driver)
    if not trip:
        return []

    remainingroute = trip.remainingnodes.all()

    requests = CarpoolRequest.objects.filter(status='pending')

    validrequests = []

    for req in requests:
        pickupok = iswithintwonodes(list(remainingroute), req.pickup)
        dropok = iswithintwonodes(list(remainingroute), req.dropoff)

        if pickupok and dropok:
            validrequests.append(req)

    return validrequests

def getdriverdashboard(driver):
    trip = getdriveractivetrip(driver)

    if not trip:
        return {
            "trip": None,
            "requests": [],
            "offers": []
        }

    requests = getmatchingrequestsfordriver(driver)

    offers = Offer.objects.filter(driver=driver)

    return {
        "trip": trip,
        "requests": requests,
        "offers": offers
    }