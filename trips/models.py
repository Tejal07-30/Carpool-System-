from django.db import models
from users.models import User
from network.models import Node
from network.utility import findpath


class Trip(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    startnode = models.ForeignKey(Node, related_name='tripstart', on_delete=models.CASCADE)
    endnode = models.ForeignKey(Node, related_name='tripend', on_delete=models.CASCADE)
    maxpassengers = models.IntegerField(default=3)
    currentnodeindex = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        isnew = self.pk is None
        super().save(*args, **kwargs)
        if isnew:
            path = findpath(self.startnode, self.endnode)
            if not path:
                raise ValueError("No valid path found between selected nodes.")
            TripRoute.objects.filter(trip=self).delete()
            for index, node in enumerate(path):
                TripRoute.objects.create(trip=self, node=node, order=index)

    
    def getfullroute(self):
        return list(self.routenodes.order_by('order').values_list('node_id', flat=True))

    def getremainingroute(self):
        return list(
            self.routenodes
            .filter(visited=False)
            .order_by('order')
            .values_list('node_id', flat=True)
        )

    def getcurrentnode(self):
        route = self.routenodes.order_by('order')
        if not route.exists():
            return self.startnode
        idx = min(self.currentnodeindex, route.count() - 1)
        return route[idx].node

    def updatecurrentnode(self, nodeid):
        from carpool.models import CarpoolOffer, Wallet
        fullroute = self.getfullroute()
        if nodeid not in fullroute:
            raise ValueError("Node is not part of this trip's route.")

        newindex = fullroute.index(nodeid)
        if newindex < self.currentnodeindex:
            raise ValueError("Cannot go backwards on the route.")

        self.currentnodeindex = newindex
        self.routenodes.filter(order__lte=newindex).update(visited=True)
        self.save()

        if nodeid == self.endnode_id:
            insufficientuser = self._checkbalances()
            if insufficientuser:
                raise ValueError(f'{insufficientuser} has insufficient wallet balance. Trip cannot be completed.')
            self._processpayments()
            self.status = 'completed'
            self.save()

    def _checkbalances(self):
        from carpool.models import CarpoolOffer, Wallet, Transaction
        acceptedoffers = self.offers.filter(status='accepted').select_related('request__passenger')
        for offer in acceptedoffers:
            passenger = offer.request.passenger
            pwallet, _ = Wallet.objects.get_or_create(user=passenger)
            if pwallet.balance < offer.fare:
                return passenger.username
        return None

    def _processpayments(self):
        from carpool.models import CarpoolOffer, Wallet, Transaction
        acceptedoffers = self.offers.filter(status='accepted').select_related('request__passenger')
        driverwallet, _ = Wallet.objects.get_or_create(user=self.driver)
        for offer in acceptedoffers:
            passenger = offer.request.passenger
            fare = offer.fare
            pwallet, _ = Wallet.objects.get_or_create(user=passenger)
            pwallet.balance -= fare
            pwallet.save()
            Transaction.objects.create(
                user=passenger, trip=self, amount=fare,
                type='debit', description=f'Fare for trip #{self.id}'
            )
            driverwallet.balance += fare
            driverwallet.save()
            Transaction.objects.create(
                user=self.driver, trip=self, amount=fare,
                type='credit', description=f'Earnings from trip #{self.id}'
            )
            offer.request.status = 'confirmed'
            offer.request.save()

    def getcurrentpassengercount(self):
        from carpool.models import CarpoolOffer
        return CarpoolOffer.objects.filter(trip=self, status='accepted').count()

    def __str__(self):
        return f"Trip #{self.id} – {self.driver.username} ({self.startnode} → {self.endnode})"


class TripRoute(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='routenodes')
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    order = models.IntegerField()
    visited = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.trip} – {self.node} (order {self.order}, visited={self.visited})"
