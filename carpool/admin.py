from django.contrib import admin
from .models import CarpoolRequest, CarpoolOffer, Wallet, Transaction

@admin.register(CarpoolRequest)
class CarpoolRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'pickupnode', 'dropoffnode', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('passenger__username',)

@admin.register(CarpoolOffer)
class CarpoolOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'request', 'fare', 'detour', 'status')
    list_filter = ('status',)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'amount', 'type', 'description', 'timestamp')
    list_filter = ('type',)
    search_fields = ('user__username',)
