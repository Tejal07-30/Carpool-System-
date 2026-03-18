from django.contrib import admin
from .models import Trip, TripRoute


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    listdisplay = ('id', 'driver', 'startnode', 'endnode', 'status')


@admin.register(TripRoute)
class TripRouteAdmin(admin.ModelAdmin):
    listdisplay = ('trip', 'node', 'order', 'visited')