from django.contrib import admin
from .models import Trip, TripRoute

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'startnode', 'endnode', 'status', 'maxpassengers', 'created_at')
    list_filter = ('status',)
    search_fields = ('driver__username',)

@admin.register(TripRoute)
class TripRouteAdmin(admin.ModelAdmin):
    list_display = ('trip', 'node', 'order', 'visited')
    list_filter = ('visited',)
