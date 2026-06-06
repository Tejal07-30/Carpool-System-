from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Trip, TripRoute
from network.models import Node
from network.models import ServiceConfig
from network.utility import findpath

@login_required
def createtrip(request):
    if request.user.role != 'driver':
        return redirect('passengerdashboard')

    cfg = ServiceConfig.get()
    if not cfg.service_enabled:
        return render(request, 'driver/trip_create.html', {
            'nodes': Node.objects.all(),
            'error': 'The carpooling service is currently suspended by the administrator.',
        })

    nodes = Node.objects.all()
    error = None

    if request.method == 'POST':
        startid = request.POST.get('startnode')
        endid = request.POST.get('endnode')
        maxpax = request.POST.get('maxpassengers', 3)

        if startid == endid:
            error = 'Start and end nodes cannot be the same.'
        else:
            try:
                start = Node.objects.get(id=startid)
                end = Node.objects.get(id=endid)
                path = findpath(start, end)
                if not path:
                    error = f'No route exists from {start.name} to {end.name}.'
                else:
                    trip = Trip.objects.create(
                        driver=request.user,
                        startnode=start,
                        endnode=end,
                        maxpassengers=int(maxpax),
                    )
                    return redirect('driverdashboard')
            except Node.DoesNotExist:
                error = 'Invalid node selected.'

    return render(request, 'driver/trip_create.html', {'nodes': nodes, 'error': error})

@require_POST
@login_required
def canceltrip(request, tripid):
    trip = get_object_or_404(Trip, id=tripid, driver=request.user)
    if trip.status == 'active':
        trip.status = 'cancelled'
        trip.save()
        from carpool.models import CarpoolOffer
        trip.offers.filter(status='pending').update(status='rejected')
    return redirect('driverdashboard')

@api_view(['POST'])
def updatetripnode(request, tripid):
    try:
        trip = Trip.objects.get(id=tripid)
        if trip.driver != request.user:
            return Response({'error': 'Not your trip.'}, status=403)
        nodeid = request.data.get('nodeid')
        if not nodeid:
            return Response({'error': 'nodeid is required.'}, status=400)
        trip.updatecurrentnode(int(nodeid))
        return Response({
            'message': 'Location updated.',
            'currentnode': trip.getcurrentnode().name,
            'status': trip.status,
        })
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found.'}, status=404)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)

@login_required
def tripdetail(request, tripid):
    trip = get_object_or_404(Trip, id=tripid, driver=request.user)
    route = trip.routenodes.order_by('order').select_related('node')
    from carpool.models import CarpoolOffer
    offers = CarpoolOffer.objects.filter(trip=trip).select_related(
        'request__passenger', 'request__pickupnode', 'request__dropoffnode'
    )
    return render(request, 'driver/trip_detail.html', {
        'trip': trip,
        'route': route,
        'offers': offers,
    })

@require_POST
@login_required
def updatenode_form(request, tripid):
    trip = get_object_or_404(Trip, id=tripid, driver=request.user)
    nodeid = request.POST.get('nodeid')
    if nodeid:
        try:
            trip.updatecurrentnode(int(nodeid))
        except ValueError:
            pass
    return redirect('driverdashboard')
