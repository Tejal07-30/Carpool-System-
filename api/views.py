from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from trips.models import Trip, TripRoute
from network.models import Node
from network.utility import findmatchingtrips, calculatefare
from carpool.models import CarpoolOffer, CarpoolRequest, Wallet, Transaction
from django.contrib.auth import get_user_model

User = get_user_model()


# Trip: update driver's current node

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updatelocation(request):
    tripid = request.data.get('tripid')
    nodeid = request.data.get('nodeid')

    try:
        trip = Trip.objects.get(id=tripid, driver=request.user)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found or not yours.'}, status=404)

    try:
        trip.updatecurrentnode(int(nodeid))
    except (ValueError, TypeError) as e:
        return Response({'error': str(e)}, status=400)

    return Response({
        'message': 'Location updated.',
        'currentnode': trip.getcurrentnode().name,
        'status': trip.status,
    })

# Passenger: find matching trips for a pickup or drop

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def findtrips(request):
    pickupid = request.data.get('pickup')
    dropid = request.data.get('drop')

    try:
        pickup = Node.objects.get(id=pickupid)
        drop = Node.objects.get(id=dropid)
    except Node.DoesNotExist:
        return Response({'error': 'Invalid node IDs.'}, status=400)

    trips = findmatchingtrips(pickup, drop)
    data = []
    for trip in trips:
        faredata = calculatefare(trip, pickup, drop)
        data.append({
            'tripid': trip.id,
            'driver': trip.driver.username,
            'currentnode': trip.getcurrentnode().name,
            'available_seats': trip.maxpassengers - trip.getcurrentpassengercount(),
            'fare': faredata['fare'],
            'detour': faredata['detour'],
        })
    return Response(data)


# Driver: records incoming carpool requests 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driverrequests(request):
    try:
        trip = Trip.objects.get(driver=request.user, status='active')
    except Trip.DoesNotExist:
        return Response({'error': 'No active trip.'}, status=404)

    from network.utility import getremainingnodes
    remaining = getremainingnodes(trip)
    routeids = [n.id for n in remaining]

    pendingreqs = CarpoolRequest.objects.filter(status='pending').select_related(
        'passenger', 'pickupnode', 'dropoffnode'
    )

    data = []
    for req in pendingreqs:
        if req.pickupnode.id not in routeids or req.dropoffnode.id not in routeids:
            continue
        if routeids.index(req.pickupnode.id) >= routeids.index(req.dropoffnode.id):
            continue
        faredata = calculatefare(trip, req.pickupnode, req.dropoffnode)
        data.append({
            'requestid': req.id,
            'passenger': req.passenger.username,
            'pickup': req.pickupnode.name,
            'drop': req.dropoffnode.name,
            'fare': faredata['fare'],
            'detour': faredata['detour'],
        })

    return Response({'tripid': trip.id, 'requests': data})


# Driver: create an offer for a request

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createoffer(request):
    requestid = request.data.get('requestid')
    try:
        trip = Trip.objects.get(driver=request.user, status='active')
        req = CarpoolRequest.objects.get(id=requestid, status='pending')
    except Trip.DoesNotExist:
        return Response({'error': 'No active trip.'}, status=404)
    except CarpoolRequest.DoesNotExist:
        return Response({'error': 'Request not found.'}, status=404)

    if CarpoolOffer.objects.filter(trip=trip, request=req).exists():
        return Response({'error': 'Offer already exists.'}, status=400)

    if trip.getcurrentpassengercount() >= trip.maxpassengers:
        return Response({'error': 'Trip is full.'}, status=400)

    faredata = calculatefare(trip, req.pickupnode, req.dropoffnode)
    offer = CarpoolOffer.objects.create(
        trip=trip, request=req,
        fare=faredata['fare'],
        detour=faredata['detour'],
        status='pending',
    )
    return Response({'message': 'Offer created.', 'offerid': offer.id})


# Passenger: accept a driver's offer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acceptoffer(request):
    offerid = request.data.get('offerid')
    try:
        offer = CarpoolOffer.objects.get(id=offerid)
    except CarpoolOffer.DoesNotExist:
        return Response({'error': 'Offer not found.'}, status=404)

    if offer.request.passenger != request.user:
        return Response({'error': 'Not your request.'}, status=403)

    if offer.request.status != 'pending':
        return Response({'error': 'Request already actioned.'}, status=400)

    offer.status = 'accepted'
    offer.save()
    offer.request.offers.exclude(id=offer.id).update(status='rejected')
    offer.request.status = 'confirmed'
    offer.request.save()

    return Response({'message': 'Offer accepted.'})

# Passenger: cancel a carpool request

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelrequest(request):
    requestid = request.data.get('requestid')
    try:
        req = CarpoolRequest.objects.get(id=requestid, passenger=request.user)
    except CarpoolRequest.DoesNotExist:
        return Response({'error': 'Request not found.'}, status=404)

    req.status = 'cancelled'
    req.save()
    req.offers.update(status='rejected')
    return Response({'message': 'Request cancelled.'})

# Driver: cancel a trip 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def canceltrip(request):
    tripid = request.data.get('tripid')
    try:
        trip = Trip.objects.get(id=tripid, driver=request.user)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found.'}, status=404)

    if trip.status != 'active':
        return Response({'error': 'Trip is not active.'}, status=400)

    trip.status = 'cancelled'
    trip.save()
    trip.offers.filter(status='pending').update(status='rejected')
    return Response({'message': 'Trip cancelled.'})

# Driver: recored their own trips

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def drivertrips(request):
    trips = Trip.objects.filter(driver=request.user).order_by('-created_at')
    data = [{
        'tripid': t.id,
        'start': t.startnode.name,
        'end': t.endnode.name,
        'status': t.status,
        'currentnode': t.getcurrentnode().name,
        'passengers': t.getcurrentpassengercount(),
        'maxpassengers': t.maxpassengers,
    } for t in trips]
    return Response(data)

# Wallet: add money

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addmoney(request):
    try:
        amount = float(request.data.get('amount', 0))
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return Response({'error': 'Invalid amount.'}, status=400)

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += amount
    wallet.save()
    Transaction.objects.create(
        user=request.user, amount=amount, type='credit', description='Wallet top-up'
    )
    return Response({'message': 'Money added.', 'balance': wallet.balance})

# Wallet: get balance

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mywallet(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    return Response({'balance': wallet.balance})

# Wallet: transaction history

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mytransactions(request):
    txns = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    data = [{
        'amount': t.amount,
        'type': t.type,
        'description': t.description,
        'timestamp': t.timestamp,
        'tripid': t.trip_id,
    } for t in txns]
    return Response({'transactions': data})

# Passenger: list their requests 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def myrequests(request):
    reqs = CarpoolRequest.objects.filter(passenger=request.user).order_by('-created_at')
    data = [{
        'requestid': r.id,
        'pickup': r.pickupnode.name,
        'drop': r.dropoffnode.name,
        'status': r.status,
        'created_at': r.created_at,
    } for r in reqs]
    return Response(data)

# Driver: complete a trip and process payments

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def completetrip(request):
    try:
        trip = Trip.objects.get(driver=request.user, status='active')
    except Trip.DoesNotExist:
        return Response({'error': 'No active trip.'}, status=404)

    offers = trip.offers.filter(status='accepted').select_related(
        'request__passenger'
    )

    for offer in offers:
        passenger = offer.request.passenger
        wallet, _ = Wallet.objects.get_or_create(user=passenger)
        if wallet.balance < offer.fare:
            return Response({
                'error': f'{passenger.username} has insufficient balance.'
            }, status=400)

    driverwallet, _ = Wallet.objects.get_or_create(user=request.user)
    for offer in offers:
        passenger = offer.request.passenger
        fare = offer.fare
        pwallet, _ = Wallet.objects.get_or_create(user=passenger)

        pwallet.balance -= fare
        pwallet.save()
        Transaction.objects.create(
            user=passenger, trip=trip, amount=fare,
            type='debit', description=f'Fare for trip #{trip.id}'
        )

        driverwallet.balance += fare
        driverwallet.save()
        Transaction.objects.create(
            user=trip.driver, trip=trip, amount=fare,
            type='credit', description=f'Earnings from trip #{trip.id}'
        )

    trip.status = 'completed'
    trip.save()
    return Response({'message': 'Trip completed and payments processed.'})
