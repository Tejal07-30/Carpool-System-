from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from trips.models import Trip, TripRoute
from network.models import Node
from network.utility import findmatchingtrips, calculatefare
from carpool.models import CarpoolOffer, CarpoolRequest, Wallet, Transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from carpool.services import getdriverdashboard


@api_view(['POST'])
def updatelocation(request):
    tripid = request.data.get('tripid')
    node_id = request.data.get('node_id')

    try:
        trip = Trip.objects.get(id=tripid)
        node = Node.objects.get(id=node_id)#error with nodeid (cannot change)
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
    pickupid = request.data.get('pickup')
    dropid = request.data.get('drop')

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
            'currentnode': trip.getcurrentnode().name,
            'available_seats': trip.maxpassengers - trip.passengers.count(),
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

    requestid = request.data.get('requestid') or request.POST.get('requestid')
    tripid = request.data.get('tripid') or request.POST.get('tripid')

    if not requestid or not tripid:
        return Response({'error': 'Missing requestid or tripid'})

    try:
        requestobj = CarpoolRequest.objects.get(id=requestid)
        trip = Trip.objects.get(id=tripid)
    except:
        return Response({'error': 'Invalid request or trip'})

    CarpoolOffer.objects.create(
        request=requestobj,
        trip=trip,
        status='pending',
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

    rider = offer.request.passenger   
    driver = offer.trip.driver

    pickup = offer.request.pickupnode
    drop = offer.request.dropoffnode

    faredata = calculatefare(offer.trip, pickup, drop)
    fare = faredata['fare']

    riderwallet, _ = Wallet.objects.get_or_create(user=rider)
    driverwallet, _ = Wallet.objects.get_or_create(user=driver)

    if riderwallet.balance < fare:
        return Response({'error': 'Insufficient balance'})

    riderwallet.balance -= fare
    riderwallet.save()

    driverwallet.balance += fare
    driverwallet.save()

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

@login_required
def driverrequests(request):

    try:
       trip = Trip.objects.filter(
            driver=request.user
        ).order_by('-created_at').first()
    except:
        return render(request, "driver/requests.html", {
            "requests": [],
            "error": "No active trip found"
        })

    requests = CarpoolRequest.objects.filter(status='pending')

    data = []

    for req in requests:
        matchingtrips = findmatchingtrips(req.pickupnode, req.dropoffnode)

        print("TRIP:", trip.id if trip else None)
        print("MATCHING:", [t.id for t in matchingtrips])

        if True:
            faredata = calculatefare(trip, req.pickupnode, req.dropoffnode)

            data.append({
                'requestid': req.id,
                'passenger': req.passenger.username,
                'pickup': req.pickupnode.name,
                'drop': req.dropoffnode.name,
                'fare': faredata['fare'],
                'detour': faredata['detour']
            })

    return render(request, "driver/requests.html", {
        "requests": data,
        "trip": trip  
    })
@login_required
def driveroffers(request):

    try:
        trip = Trip.objects.filter(
        driver=request.user,
        status='active'
        ).first()
        
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
    User = get_user_model()
@api_view(['POST'])
def createrequest(request):
    userid = request.data.get('userid')
    pickupid = request.data.get('pickupnode')
    dropid = request.data.get('dropoffnode')

    try:
        user = User.objects.get(id=userid)
        pickupnode = Node.objects.get(id=pickupid)
        dropoffnode = Node.objects.get(id=dropid)
    except:
        return Response({'error': 'Invalid nodes'})
    pickuproutes = TripRoute.objects.filter(node=pickupnode)
    droproutes = TripRoute.objects.filter(node=dropoffnode)
    valid = False

    for p in pickuproutes:
        for d in droproutes:
            if p.trip == d.trip and p.order < d.order:
                valid = True
                break

    if not valid:
        return Response({'error': 'Invalid nodes'})
    carpoolrequest = CarpoolRequest.objects.create(
        passenger=user,  
        pickupnode=pickupnode,
        dropoffnode=dropoffnode,
        status='pending'
    )

    return Response({
        'message': 'Request created',
        'requestid': carpoolrequest.id
    })
@api_view(['POST'])
def myrequests(request):
    userid = request.data.get('userid')

    try:
        user = User.objects.get(id=userid)
    except:
        return Response({'error': 'Invalid user'})

    requests = CarpoolRequest.objects.filter(passenger=user)

    data = []
    for req in requests:
        data.append({
            'requestid': req.id,
            'pickup': req.pickupnode.name,
            'drop': req.dropoffnode.name,
            'status': req.status,
            'created_at': req.created_at
        })

    return Response(data)
@api_view(['POST'])
def completetrip(request):
    tripid = request.data.get('tripid')
    try:
        trip = Trip.objects.get(id=tripid)
    except Trip.DoesNotExist:
        return Response({"error": "Trip not found"})
    print("Offers found:", offers.count())
    print("Trip ID received:", tripid)

    if trip.status != 'active':
        return Response({"error": "Trip not active"})

    offers = trip.offers.filter(status='accepted')

    for offer in offers:
        passenger = offer.request.passenger
        fare = offer.fare

        wallet = passenger.wallet
        if wallet.balance < fare:
            return Response({
                "error": f"{passenger.username} has insufficient balance"
            })
    for offer in offers:
        passenger = offer.request.passenger
        fare = offer.fare
        passenger.wallet.balance -= fare
        passenger.wallet.save()

        Transaction.objects.create(
            user=passenger,
            trip=trip,
            amount=fare,
            type='debit',
            description='Trip fare'
        )
        driverwallet = trip.driver.wallet
        driverwallet.balance += fare
        driverwallet.save()

        Transaction.objects.create(
            user=trip.driver,
            trip=trip,
            amount=fare,
            type='credit',
            description='Trip earning'
        )

    trip.status = 'completed'
    trip.save()

    return Response({"message": "Trip completed successfully"})
@api_view(['GET'])
def mywallet(request):
    wallet = request.user.wallet

    return Response({
        "balance": wallet.balance
    })
@api_view(['GET'])
def mytransactions(request):
    transactions = Transaction.objects.filter(user=request.user)

    data = []

    for t in transactions:
        data.append({
            "amount": t.amount,
            "type": t.type,
            "description": t.description,
            "date": t.created_at
        })

    return Response({"transactions": data})

def driverdashboardapi(request):
    data = getdriverdashboard(request.user)

    return JsonResponse({
        "trip": str(data["trip"]),
        "requests": [r.id for r in data["requests"]],
        "offers": [o.id for o in data["offers"]],
    })