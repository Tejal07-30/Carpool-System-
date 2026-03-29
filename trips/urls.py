from django.urls import path
from .views import updatetripnode, completetrip

urlpatterns = [
    path('updatenode/<int:tripid>/', updatetripnode),
    path('completetrip/<int:tripid>/', completetrip)
]