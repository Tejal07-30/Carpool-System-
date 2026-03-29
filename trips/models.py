from django.db import models
from users.models import User 
from network.models import Node 
from network.utility import findpath

class Trip(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE)
    startnode = models.ForeignKey(Node, related_name='tripstart', on_delete=models.CASCADE)
    endnode = models.ForeignKey(Node, related_name='tripend', on_delete=models.CASCADE)

    maxpassengers = models.IntegerField()
    currentnode = models.ForeignKey(Node, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
    max_length=10,
    choices=STATUS_CHOICES,
    default='active'
    )

    def save(self, *args, **kwargs):
        isnew = self.pk is None
        super().save(*args, **kwargs)

        if isnew:
            print("SAVE FUNCTION CALLED")
            path = findpath(self.startnode, self.endnode)
            print("PATH:", path)

            if path:
                for index, node in enumerate(path):
                    TripRoute.objects.create(
                        trip=self,
                        node=node,
                        order=index
                    )


class TripRoute(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    node = models.ForeignKey(Node, on_delete=models.CASCADE)

    order = models.IntegerField()   
    visited = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.trip} - {self.node} ({self.order})"
    
