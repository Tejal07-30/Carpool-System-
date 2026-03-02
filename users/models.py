from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    role_choices = (
        ('driver','Driver'),
        ('passenger','Passenger'),
        ('admin','Admin'),
    )
    role = models.CharField(max_length=10,choices=role_choices, default='passenger')

    def __str__(self):
        return self.username


