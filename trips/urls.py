from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.createtrip, name='createtrip'),
    path('<int:tripid>/cancel/', views.canceltrip, name='canceltrip'),
    path('<int:tripid>/detail/', views.tripdetail, name='tripdetail'),
    path('<int:tripid>/updatenode/', views.updatetripnode, name='updatetripnode'),
    path('<int:tripid>/advance/', views.updatenode_form, name='advancenode'),
]
