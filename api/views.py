from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from trips.models import Trip, TripRoute
from network.models import Node
from network.utility import findmatchingtrips, calculatefare
from carpool.models import CarpoolOffer, CarpoolRequest, Wallet, Transaction


@api_view(['POST'])
def updatelocation(request):
    tripid = request.data.get('tripid')
    nodeid = request.data.get('nodeid')

    try:
        trip = Trip.objects.get(id=tripid)
        node = Node.objects.get(id=nodeid)
    except:
        return Response({'error': 'Invalid trip or node'})

    try:
        currentroute = TripRoute.objects.get(trip=trip, node=node)
    except:
        return Response({'error': 'Node not part of this trip route'})

    trip.currentnode = node
    if node == trip.endnode:
        trip.status = 'completed'
    trip.save()

    TripRoute.objects.filter(
        trip=trip,
        order__lte=currentroute.order
    ).update(visited=True)

    return Response({
        'message': 'Location updated successfully',
        'currentnode': node.name
    })
@api_view(['POST'])
def findtrips(request):
    pickupid = request.data.get('pickupnode')
    dropid = request.data.get('dropoffnode')

    try:
        pickup = Node.objects.get(id=pickupid)
        drop = Node.objects.get(id=dropid)
    except:
        return Response({'error': 'Invalid nodes'})

    trips = findmatchingtrips(pickup, drop)

    data = []
    for trip in trips:
        faredata = calculatefare(trip, pickup, drop)
        data.append({
            'tripid': trip.id,
            'driver': trip.driver.username,
            'currentnode': trip.currentnode.name,
            'fare': faredata['fare'],
            'detour': faredata['detour'],
        })
    print("Pickup:", pickup.id)
    print("Drop:", drop.id)

    for trip in Trip.objects.all():
        print("Trip:", trip.id, trip.startnode, "→", trip.endnode)

    return Response(data)
@api_view(['POST'])
def createoffer(request):
    tripid = request.data.get('tripid')
    requestid = request.data.get('requestid')

    try:
        trip = Trip.objects.get(id=tripid)
        carpoolrequest = CarpoolRequest.objects.get(id=requestid)
    except:
        return Response({'error': 'Invalid data'})

    offer = CarpoolOffer.objects.create(
        trip=trip,
        request=request_obj,
        fare=fare_data['fare']
    )

    return Response({'message': 'Offer created'})
@api_view(['POST'])
def acceptoffer(request):
    offerid = request.data.get('offerid')

    try:
        offer = CarpoolOffer.objects.get(id=offerid)
    except:
        return Response({'error': 'Invalid offer'})

    offer.status = 'accepted'
    offer.save()

    CarpoolOffer.objects.filter(
        request=offer.request
    ).exclude(id=offer.id).update(status='rejected')

    offer.request.status = 'accepted'
    offer.request.save()

    rider = offer.request.user   
    driver = offer.trip.driver

    pickup = offer.request.pickupnode
    drop = offer.request.dropoffnode

    faredata = calculatefare(offer.trip, pickup, drop)
    fare = faredata['fare']

    rider_wallet, _ = Wallet.objects.get_or_create(user=rider)
    driver_wallet, _ = Wallet.objects.get_or_create(user=driver)

    if rider_wallet.balance < fare:
        return Response({'error': 'Insufficient balance'})

    rider_wallet.balance -= fare
    rider_wallet.save()

    driver_wallet.balance += fare
    driver_wallet.save()

    Transaction.objects.create(
        user=rider,
        amount=fare,
        type='debit',
        description='Trip payment'
    )

    Transaction.objects.create(
        user=driver,
        amount=fare,
        type='credit',
        description='Trip earning'
    )

    return Response({'message': 'Offer accepted and payment processed'})
@api_view(['POST'])
def cancelrequest(request):
    requestid = request.data.get('requestid')

    try:
        carpoolrequest = CarpoolRequest.objects.get(id=requestid)
    except:
        return Response({'error': 'Invalid request'})

    carpoolrequest.status = 'cancelled'
    carpoolrequest.save()
    CarpoolOffer.objects.filter(
        request=carpoolrequest
    ).update(status='rejected')

    return Response({'message': 'Request cancelled'})
@api_view(['GET'])
def driverrequests(request):
    tripid = request.GET.get('tripid')

    try:
        trip = Trip.objects.get(id=tripid)
    except:
        return Response({'error': 'Invalid trip'})

    requests = CarpoolRequest.objects.filter(status='pending')

    data = []

    for req in requests:
        matchingtrips = findmatchingtrips(req.pickupnode, req.dropoffnode)

        if trip in matchingtrips:
            faredata = calculatefare(trip, req.pickupnode, req.dropoffnode)

            data.append({
                'requestid': req.id,
                'passenger': req.passenger.username,
                'pickup': req.pickupnode.name,
                'drop': req.dropoffnode.name,
                'fare': faredata['fare'],
                'detour': faredata['detour']
            })

    return Response(data)
@api_view(['GET'])
def driveroffers(request):
    tripid = request.GET.get('tripid')

    try:
        trip = Trip.objects.get(id=tripid)
    except:
        return Response({'error': 'Invalid trip'})

    offers = CarpoolOffer.objects.filter(trip=trip)

    data = []

    for offer in offers:
        data.append({
            'offerid': offer.id,
            'passenger': offer.request.passenger.username,
            'pickup': offer.request.pickupnode.name,
            'drop': offer.request.dropoffnode.name,
            'status': offer.status
        })

    return Response(data)
@api_view(['POST'])
def canceltrip(request):
    tripid = request.data.get('tripid')

    try:
        trip = Trip.objects.get(id=tripid)
    except:
        return Response({'error': 'Invalid trip'})

    trip.status = 'cancelled'
    trip.save()

    return Response({'message': 'Trip cancelled'})
@api_view(['GET'])
def drivertrips(request):
    trips = Trip.objects.all()

    data = []

    for trip in trips:
        data.append({
            'tripid': trip.id,
            'start': trip.startnode.name,
            'end': trip.endnode.name,
            'status': trip.status
        })

    return Response(data)

@api_view(['POST'])
def addmoney(request):
    amount = request.data.get('amount')

    if not amount:
        return Response({'error': 'Amount required'})

    amount = float(amount)
    user = request.user   
    wallet, created = Wallet.objects.get_or_create(user=user)
    wallet.balance += amount
    wallet.save()
    Transaction.objects.create(
        user=user,
        amount=amount,
        type='credit',
        description='Wallet top-up'
    )

    return Response({
        'message': 'Money added',
        'balance': wallet.balance
    })
@api_view(['POST'])
def createrequest(request):
    userid = request.data.get('passenger')
    pickupid = request.data.get('pickupnode')
    dropid = request.data.get('dropoffnode')

    try:
        user = User.objects.get(id=userid)
        pickup = Node.objects.get(id=pickupid)
        drop = Node.objects.get(id=dropid)
    except:
        return Response({'error': 'Invalid nodes'})

    carpoolrequest = CarpoolRequest.objects.create(
        passenger=user,  
        pickupnode=pickup,
        dropoffnode=drop,
        status='pending'
    )

    return Response({
        'message': 'Request created',
        'requestid': carpoolrequest.id
    })