from django.contrib import admin
from .models import CarpoolRequest, CarpoolOffer
from .models import Wallet, Transaction

@admin.register(CarpoolRequest)
class CarpoolRequestAdmin(admin.ModelAdmin):
    listdisplay = ('id', 'passenger', 'pickupnode', 'dropoffnode', 'status')
admin.site.register(CarpoolOffer)
admin.site.register(Wallet)
admin.site.register(Transaction)