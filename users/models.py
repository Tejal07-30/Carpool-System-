from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    rolechoices = (
        ('driver','Driver'),
        ('passenger','Passenger'),
        ('admin','Admin'),
    )
    role = models.CharField(max_length=10,choices=rolechoices, default='passenger')

    def __str__(self):
        return self.username


