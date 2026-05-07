# pickups/urls.py
from django.urls import path
from . import views

app_name = 'pickups'

urlpatterns = [
    path('dodaj/', views.create_pickup, name='create'), 
    path('sukces/', views.pickup_success, name='success'), 
    path('lista/', views.pickup_list, name='pickup_list'),
    # API endpoints
    path('api/lokalizacja/<int:location_id>/pojemniki/', views.api_get_location_bins, name='api_location_bins'),
    path('api/mpk/<int:mpk_id>/lokalizacje/', views.api_get_mpk_locations, name='api_mpk_locations'),
]