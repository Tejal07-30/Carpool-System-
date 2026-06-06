from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from users.models import User
from network.models import Node
from trips.models import Trip

# CarpoolRequest – submitted by a passenger

class CarpoolRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carpool_requests')
    pickupnode = models.ForeignKey(Node, related_name='pickuprequests', on_delete=models.CASCADE)
    dropoffnode = models.ForeignKey(Node, related_name='dropoffrequests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request #{self.id} – {self.passenger.username} ({self.pickupnode} → {self.dropoffnode}) [{self.status}]"


# CarpoolOffer – created by a driver for a request

class CarpoolOffer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='offers')
    request = models.ForeignKey(CarpoolRequest, on_delete=models.CASCADE, related_name='offers')
    fare = models.FloatField(default=0)
    detour = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Offer #{self.id} – Trip {self.trip_id} → Request {self.request_id} [{self.status}]"

# Wallet – one per user and it is auto-created on signup

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username}'s wallet – ₹{self.balance}"

# Transaction – record entry for every money movement

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.FloatField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.type} ₹{self.amount} – {self.description}"


# Auto-create wallet when a new user is saved

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(user=instance)
