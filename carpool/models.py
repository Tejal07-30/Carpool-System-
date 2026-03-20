from django.db import models
from users.models import User
from network.models import Node
from trips.models import Trip
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class CarpoolRequest(models.Model):
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)

    pickupnode = models.ForeignKey(
        Node,
        related_name='pickuprequests',
        on_delete=models.CASCADE
    )

    dropoffnode = models.ForeignKey(
        Node,
        related_name='dropoffrequests',
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger} ({self.pickupnode} → {self.dropoffnode})"
class CarpoolOffer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    request = models.ForeignKey(CarpoolRequest, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'  
    )
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.balance}"
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey('trips.Trip', on_delete=models.SET_NULL, null=True, blank=True)

    amount = models.FloatField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.type}"
@receiver(post_save, sender=User)
def createwallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)