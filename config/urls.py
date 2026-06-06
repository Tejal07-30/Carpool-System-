from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'driver':
            return redirect('driverdashboard')
        return redirect('passengerdashboard')
    return redirect('login')

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('', include('carpool.urls')),
    path('trips/', include('trips.urls')),
    path('api/', include('api.urls')),
    path('accounts/', include('allauth.urls')),
]
