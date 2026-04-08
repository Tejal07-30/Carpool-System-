from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from trips.models import Trip
from .models import CarpoolOffer, CarpoolRequest, Transaction, Wallet
from .utility import computeoffer
from network.models import Node
from carpool.models import Transaction
from network.utility import findmatchingtrips, calculatefare

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('driverdashboard')

    return render(request, "login.html")
'''def createofferforrequest(trip, carpoolrequest):
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
        createofferforrequest(trip, req)'''

@login_required
def driverdashboard(request):
    trip = Trip.objects.filter(
        driver=request.user,
        status='active'
    ).first()

    if not trip:
        trip = Trip.objects.filter(driver=request.user).first()
    requests = []
    offers = []
    acceptedoffers = []

    if trip:
       
        offers = CarpoolOffer.objects.filter(trip=trip)

        acceptedoffers = offers.filter(status="accepted")

        existingoffers = offers.values_list('request_id', flat=True)

        allrequests = CarpoolRequest.objects.all()

        routenodes = list(trip.routenodes.values_list('node_id', flat=True))

        for req in allrequests:
            alreadyoffered = req.id in existingoffers
            pickupid = req.pickupnode.id
            dropid = req.dropoffnode.id

            if pickupid == dropid:
                continue

            if pickupid in routenodes and dropid in routenodes:

                pickupindex = routenodes.index(pickupid)
                dropindex = routenodes.index(dropid)

                if pickupindex < dropindex:

                    faredata = calculatefare(
                        trip,
                        req.pickupnode,
                        req.dropoffnode
                    )

                    requests.append({
                        "request": req,
                        "fare": faredata["fare"],
                        "detour": faredata["detour"],
                        "already_offered": alreadyoffered
                    })

    return render(request, "driver/dashboard.html", {
        "trip": trip,
        "requests": requests,
        "offers": offers,
        "acceptedoffers": acceptedoffers
    })
@login_required
def createrequest(request):
    if request.method == 'POST':
        pickupid = request.POST.get("pickup")
        dropoffid = request.POST.get("dropoff")

        if not pickupid or not dropoffid:
            return redirect("createrequest")
        if pickupid == dropoffid:
            return redirect("createrequest")

        pickup = Node.objects.get(id=pickupid)
        dropoff = Node.objects.get(id=dropoffid)

        existing = CarpoolRequest.objects.filter(
            passenger=request.user,
            pickupnode=pickup,
            dropoffnode=dropoff,
            status="pending"
        )

        if existing.exists():
            return redirect('passengerrequests')

        CarpoolRequest.objects.create(
            passenger=request.user,
            pickupnode=pickup,
            dropoffnode=dropoff,
            status='pending'
        )
        return redirect("passengerrequests")
        
    nodes = Node.objects.all()

    return render(request, "passenger/createrequest.html", {
        "nodes": nodes
    })

def passengeroffers(request):
    offers = CarpoolOffer.objects.filter(
        request__passenger=request.user
    )

    return render(request, 'passenger/offers.html', {
        'offers': offers
    })


def walletview(request):
    wallet = request.user.wallet
    transactions = Transaction.objects.filter(user=request.user)

    return render(request, 'wallet/wallet.html', {
        'balance': wallet.balance,
        'transactions': transactions
    })

'''@require_POST
@login_required
def driverofferaccept(request):
    offerid = request.POST.get("offerid")
    offer = CarpoolOffer.objects.get(id=offerid)
    if offer.trip.driver != request.user:
        return redirect("driverdashboard")

    offer.status = "accepted"
    offer.save()
    offer.request.status = "confirmed"
    offer.request.save()
    return redirect("driverdashboard")

@require_POST
@login_required
def driverofferreject(request):
    offerid = request.POST.get("offerid")
    offer = CarpoolOffer.objects.get(id=offerid)
    if offer.trip.driver != request.user:
        return redirect("driverdashboard")

    offer.status = "rejected"
    offer.save()

    return redirect("driverdashboard")'''
@login_required
def passengerrequests(request):
    if request.method == "POST":
        pickupid = request.POST.get("pickupnode")
        dropid = request.POST.get("dropoffnode")

        if pickupid == dropid:
            return redirect('passengerrequests')

        try:
            pickupnode = Node.objects.get(id=pickupid)
            dropoffnode = Node.objects.get(id=dropid)
        except Node.DoesNotExist:
            return redirect('passengerrequests')

        CarpoolRequest.objects.create(
            passenger=request.user,
            pickupnode=pickupnode,
            dropoffnode=dropoffnode,
            status="pending"
        )

        return redirect('passengerrequests')

    requests = CarpoolRequest.objects.filter(passenger=request.user)

    nodes = Node.objects.all()

    return render(request, "passenger/requests.html", {
        "requests": requests,
        "nodes": nodes
    })
@require_POST
@login_required
def confirmoffer(request):
    offerid = request.POST.get("offerid")
    offer = CarpoolOffer.objects.get(id=offerid)
    if offer.request.passenger != request.user:
        return redirect("passengerrequests")
    offer.status = "accepted"
    offer.save()
    CarpoolOffer.objects.filter(
        request=offer.request
    ).exclude(id=offer.id).update(status="rejected")
    offer.request.status = "confirmed"
    offer.request.save()

    return redirect("passengerrequests")

@require_POST
@login_required
def createoffer(request):

    requestid = request.POST.get("requestid")
    fare = request.POST.get("fare")
    detour = request.POST.get("detour")

    carpoolrequest = CarpoolRequest.objects.get(id=requestid)

    trip = Trip.objects.filter(
        driver=request.user,
        status='active'
    ).first()

    existingoffer = CarpoolOffer.objects.filter(
        driver=request.user,
        request=carpool_request
    )  

    if existingoffer.exists():
        return redirect("driverdashboard")

    if not trip:
        return redirect("driverdashboard")

    if trip.getcurrentpassengercount() >= trip.maxpassengers:
        return redirect("driverdashboard")

    if CarpoolOffer.objects.filter(trip=trip, request=carpoolrequest).exists():
        return redirect("driverdashboard")

    routeids = list(trip.routenodes.values_list('node_id', flat=True))

    if (
        carpoolrequest.pickupnode.id not in routeids or
        carpoolrequest.dropoffnode.id not in routeids or
        routeids.index(carpoolrequest.pickupnode.id) >= routeids.index(carpoolrequest.dropoffnode.id)
    ):
        return redirect("driverdashboard")

    CarpoolOffer.objects.create(
        trip=trip,
        request=carpoolrequest,
        fare=fare,
        detour=detour,
        status="pending"
    )

    return redirect("driverdashboard")
@login_required
def walletview(request):
    wallet = request.user.wallet
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')

    return render(request, 'wallet/wallet.html', {
        'balance': wallet.balance,
        'transactions': transactions
    })
@require_POST
@login_required
def addmoneyview(request):
    amount = request.POST.get("amount")

    if not amount:
        return redirect("wallet")

    amount = float(amount)

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += amount
    wallet.save()

    Transaction.objects.create(
        user=request.user,
        amount=amount,
        type='credit',
        description='Wallet top-up'
    )

    return redirect("wallet")
@require_POST
@login_required
def cancelrequestview(request):
    requestid = request.POST.get("requestid")

    try:
        req = CarpoolRequest.objects.get(id=requestid)
    except:
        return redirect("passengerrequests")

    if req.passenger != request.user:
        return redirect("passengerrequests")

    req.status = "cancelled"
    req.save()

    CarpoolOffer.objects.filter(request=req).update(status="rejected")
    return redirect("passengerrequests")
@require_POST
@login_required
def completetripview(request):
    trip = Trip.objects.filter(
        driver=request.user,
        status='active'
    ).first()

    if not trip:
        return redirect("driverdashboard")

    offers = trip.offers.filter(status='accepted')

    for offer in offers:
        passenger = offer.request.passenger
        if passenger.wallet.balance < offer.fare:
            return redirect("driverdashboard")

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

        driverwallet = request.user.wallet
        driverwallet.balance += fare
        driverwallet.save()

        Transaction.objects.create(
            user=request.user,
            trip=trip,
            amount=fare,
            type='credit',
            description='Trip earning'
        )

    trip.status = "completed"
    trip.save()

    return redirect("driverdashboard")

def acceptoffer(request, offerid):
    from django.http import JsonResponse

    offer = CarpoolOffer.objects.get(id=offerid)
    trip = offer.trip
    
    if trip.getcurrentpassengercount() >= trip.maxpassengers:
        return JsonResponse({'error': 'Trip is full'})
    
    offer.status = 'accepted'
    offer.save()

    CarpoolOffer.objects.filter(
        request=offer.request
    ).exclude(id=offer.id).update(status='rejected')
    

    offer.request.status = 'confirmed'
    offer.request.save()

    return redirect("requests")

def rejectoffer(request, offerid):
    offer = CarpoolOffer.objects.get(id=offerid)
    offer.status = 'rejected'
    offer.save()

    return redirect("passengerrequests")
@login_required
def passengerdashboard(request):
    requests = CarpoolRequest.objects.filter(passenger=user).order_by('-created_at').distinct()

    return render(request, "passenger/dashboard.html", {
        "requests": requests
    })
@login_required
def viewoffers(request, requestid):
    offers = CarpoolOffer.objects.filter(requestid=requestid)

    return render(request, "passenger/offers.html", {
        "offers": offers
    })
@require_POST
@login_required
def acceptdriver(request, offerid):
    offer = CarpoolOffer.objects.get(id=offerid)

    offer.status = "accepted"
    offer.save()

    CarpoolOffer.objects.filter(
        request=offer.request
    ).exclude(id=offer.id).update(status="rejected")

    offer.request.status = "accepted"
    offer.request.save()

    return redirect("passengerdashboard")


@login_required
def offerride(request, request_id):
    trip = Trip.objects.filter(
        driver=request.user,
        status='active'
    ).first()

    req = CarpoolRequest.objects.get(id=request_id)

    if CarpoolOffer.objects.filter(trip=trip, request=req).exists():
        return redirect('driverdashboard')

    if req.pickupnode == req.dropoffnode:
        return redirect('driverdashboard')

    faredata = calculatefare(
        trip,
        req.pickupnode,
        req.dropoffnode
    )

    CarpoolOffer.objects.create(
        trip=trip,
        request=req,
        fare=faredata["fare"],
        detour=faredata["detour"],
        status="pending"
    )

    return redirect('driverdashboard')

@login_required
def myrequests(request):
    userrequests = CarpoolRequest.objects.filter(passenger=request.user)

    data = []

    for req in userrequests:
        offers = CarpoolOffer.objects.filter(request=req)

        data.append({
            "request": req,
            "offers": offers
        })

    return render(request, "passenger/requests.html", {
        "data": data
    })