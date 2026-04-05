from django.db import models
from users.models import User 
from network.models import Node 
from network.utility import findpath

class Trip(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    startnode = models.ForeignKey(Node, related_name='tripstart', on_delete=models.CASCADE)
    endnode = models.ForeignKey(Node, related_name='tripend', on_delete=models.CASCADE)

    maxpassengers = models.IntegerField(default=3)
    currentnodeindex = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUSCHOICES = [
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
    max_length=10,
    choices=STATUSCHOICES,
    default='active'
    )

    def save(self, *args, **kwargs):
        isnew = self.pk is None
        super().save(*args, **kwargs)

        if isnew:
            path = findpath(self.startnode, self.endnode)

            if not path:
                raise ValueError("No valid path found")

            TripRoute.objects.filter(trip=self).delete()

            for index, node in enumerate(path):
                TripRoute.objects.create(
                    trip=self,
                    node=node,
                    order=index
                )
    def getfullroute(self):
        return list(
            self.routenodes.values_list('node_id', flat=True)
        )
    def getremainingroute(self):
        return list(
            self.routenodes
            .filter(order__gte=self.currentnodeindex)
            .values_list('node_id', flat=True)
        )
    def updatecurrentnode(self, node_id):
        route = self.getfullroute()

        if node_id not in route:
            raise ValueError("Node not in route")

        newindex = route.index(node_id)

        if newindex < self.currentnodeindex:
            raise ValueError("Cannot go backwards")

        self.currentnodeindex = newindex
        if self.currentnodeindex == len(route) - 1:
            self.status = 'completed'

        self.save()
    def getcurrentnode(self):
        route = self.routenodes.order_by('order')
        return route[self.currentnodeindex].node
    def getcurrentpassengercount(self):
        acceptedoffers = CarpoolOffer.objects.filter(
            trip=self,
            status='accepted'
        )

        return acceptedoffers.count()

class TripRoute(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='routenodes')
    node = models.ForeignKey(Node, on_delete=models.CASCADE)

    order = models.IntegerField()   
    visited = models.BooleanField(default=False)
    class Meta:
        ordering = ['order']
    def __str__(self):
        return f"{self.trip} - {self.node} ({self.order})"
    
    