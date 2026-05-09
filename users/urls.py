# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profil/',          views.profile_view,         name='profile'),
    path('zmien-haslo/',     views.change_password_view, name='change_password'),
]