# pickups/urls.py
from django.urls import path
from . import views

app_name = 'pickups'

urlpatterns = [
    path('dodaj/', views.create_pickup, name='create'), 
    path('sukces/', views.pickup_success, name='success'), 
]