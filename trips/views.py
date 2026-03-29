from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Trip
from carpool.models import CarpoolOffer
from carpool.utils import processtrippayment


@api_view(['POST'])
def updatetripnode(request, tripid):
    try:
        trip = Trip.objects.get(id=tripid)
        node_id = request.data.get("node_id")

        trip.updatecurrentnode(node_id)

        return Response({"message": "updated"})
    
    except Exception as e:
        return Response({"error": str(e)}, status=400)
@api_view(['POST'])
def completetrip(request, tripid):
    try:
        trip = Trip.objects.get(id=tripid)
        offer = CarpoolOffer.objects.get(
            trip=trip,
            status='accepted'
        )

        passenger = offer.request.passenger
        fare = offer.fare
        processtrippayment(trip, passenger, fare)
        trip.status = 'completed'
        trip.save()

        return Response({"message": "Trip completed and payment processed"})

    except Exception as e:
        return Response({"error": str(e)}, status=400)