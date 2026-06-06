from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from trips.models import Trip, TripRoute
from network.models import ServiceConfig
from network.models import Node
from network.utility import findmatchingtrips, calculatefare, getremainingnodes
from .models import CarpoolRequest, CarpoolOffer, Wallet, Transaction

# still in trial mode 
# AUTH

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == 'driver':
                return redirect('driverdashboard')
            else:
                return redirect('passengerdashboard')
        error = 'Invalid username or password.'
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# DRIVER VIEWS

@login_required
def driverdashboard(request):
    
    user = request.user

    activetrip = Trip.objects.filter(driver=user, status='active').first()
    pasttrips = Trip.objects.filter(
        driver=user, status__in=['completed', 'cancelled']
    ).order_by('-created_at')

    matchablerequests = []
    pendingoffers = []
    acceptedoffers = []

    if activetrip:
        remainingnodes = getremainingnodes(activetrip)
        routeids = [n.id for n in remainingnodes]

        allpending = CarpoolRequest.objects.filter(status='pending').select_related(
            'passenger', 'pickupnode', 'dropoffnode'
        )

        existingofferrequestids = set(
            activetrip.offers.values_list('request_id', flat=True)
        )

        for req in allpending:
            if req.pickupnode.id not in routeids or req.dropoffnode.id not in routeids:
                continue
            if routeids.index(req.pickupnode.id) >= routeids.index(req.dropoffnode.id):
                continue
            if req.pickupnode == req.dropoffnode:
                continue

            faredata = calculatefare(activetrip, req.pickupnode, req.dropoffnode)
            matchablerequests.append({
                'request': req,
                'fare': faredata['fare'],
                'detour': faredata['detour'],
                'already_offered': req.id in existingofferrequestids,
            })

        pendingoffers = activetrip.offers.filter(status='pending').select_related(
            'request__passenger', 'request__pickupnode', 'request__dropoffnode'
        )
        acceptedoffers = activetrip.offers.filter(status='accepted').select_related(
            'request__passenger', 'request__pickupnode', 'request__dropoffnode'
        )

    return render(request, 'driver/dashboard.html', {
        'activetrip': activetrip,
        'pasttrips': pasttrips,
        'matchablerequests': matchablerequests,
        'pendingoffers': pendingoffers,
        'acceptedoffers': acceptedoffers,
    })


@require_POST
@login_required
def offer_ride(request, requestid):
    
    activetrip = Trip.objects.filter(driver=request.user, status='active').first()
    if not activetrip:
        return redirect('driverdashboard')

    req = get_object_or_404(CarpoolRequest, id=requestid, status='pending')

    if CarpoolOffer.objects.filter(trip=activetrip, request=req).exists():
        return redirect('driverdashboard')

    if activetrip.getcurrentpassengercount() >= activetrip.maxpassengers:
        return redirect('driverdashboard')

    faredata = calculatefare(activetrip, req.pickupnode, req.dropoffnode)
    CarpoolOffer.objects.create(
        trip=activetrip,
        request=req,
        fare=faredata['fare'],
        detour=faredata['detour'],
        status='pending',
    )
    return redirect('driverdashboard')


@require_POST
@login_required
def complete_trip(request):
    trip = Trip.objects.filter(driver=request.user, status='active').first()
    if not trip:
        return redirect('driverdashboard')

    insufficientuser = trip._checkbalances()
    if insufficientuser:
        return render(request, 'driver/dashboard.html', {
            'error': f'{insufficientuser} has insufficient wallet balance. Top up required before completing.',
            'activetrip': trip,
        })

    trip._processpayments()
    trip.status = 'completed'
    trip.save()
    return redirect('driverdashboard')

# PASSENGER VIEWS

@login_required
def passengerdashboard(request):
    user = request.user
    requests = CarpoolRequest.objects.filter(passenger=user).order_by('-created_at')
    pendingcount = requests.filter(status='pending').count()
    confirmedcount = requests.filter(status='confirmed').count()
    cancelledcount = requests.filter(status='cancelled').count()
    return render(request, 'passenger/dashboard.html', {
        'requests': requests,
        'pendingcount': pendingcount,
        'confirmedcount': confirmedcount,
        'cancelledcount': cancelledcount,
    })


@login_required
def create_request(request):
    cfg = ServiceConfig.get()
    if not cfg.service_enabled:
        return render(request, 'passenger/createrequest.html', {
            'nodes': Node.objects.all(),
            'error': 'The carpooling service is currently suspended by the administrator.',
        })

    nodes = Node.objects.all()
    error = None

    if request.method == 'POST':
        pickupid = request.POST.get('pickupnode')
        dropoffid = request.POST.get('dropoffnode')

        if pickupid == dropoffid:
            error = 'Pickup and dropoff cannot be the same node.'
        else:
            try:
                pickup = Node.objects.get(id=pickupid)
                dropoff = Node.objects.get(id=dropoffid)

                matching = findmatchingtrips(pickup, dropoff)
                
                CarpoolRequest.objects.create(
                    passenger=request.user,
                    pickupnode=pickup,
                    dropoffnode=dropoff,
                    status='pending',
                )
                return redirect('passengerrequests')
            except Node.DoesNotExist:
                error = 'Invalid node selected.'

    return render(request, 'passenger/createrequest.html', {'nodes': nodes, 'error': error})


@login_required
def passenger_requests(request):
    
    reqs = CarpoolRequest.objects.filter(
        passenger=request.user
    ).order_by('-created_at').prefetch_related('offers__trip__driver')

    data = []
    for req in reqs:
        offers = req.offers.select_related('trip__driver')
        data.append({'request': req, 'offers': offers})

    return render(request, 'passenger/requests.html', {'data': data})


@require_POST
@login_required
def confirm_offer(request):
    
    offerid = request.POST.get('offerid')
    offer = get_object_or_404(CarpoolOffer, id=offerid)

    if offer.request.passenger != request.user:
        return redirect('passengerrequests')

    if offer.request.status != 'pending':
        return redirect('passengerrequests')

    offer.status = 'accepted'
    offer.save()
    offer.request.offers.exclude(id=offer.id).update(status='rejected')
    offer.request.status = 'confirmed'
    offer.request.save()

    return redirect('passengerrequests')


@require_POST
@login_required
def cancel_request(request):
    
    requestid = request.POST.get('requestid')
    req = get_object_or_404(CarpoolRequest, id=requestid, passenger=request.user)

    if req.status in ('pending', 'confirmed'):
        req.status = 'cancelled'
        req.save()
        req.offers.update(status='rejected')

    return redirect('passengerrequests')

# WALLET VIEWS

@login_required
def wallet_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
    })


@require_POST
@login_required
def add_money(request):
    amountstr = request.POST.get('amount', '')
    try:
        amount = float(amountstr)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return redirect('wallet')

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += amount
    wallet.save()

    Transaction.objects.create(
        user=request.user,
        amount=amount,
        type='credit',
        description='Wallet top-up',
    )
    return redirect('wallet')
