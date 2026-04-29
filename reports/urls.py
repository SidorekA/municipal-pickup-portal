from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

app_name = 'raporty'

def placeholder(request):
    return render(request, 'placeholder.html', {'title': 'Raporty'})

urlpatterns = [
    path('', login_required(placeholder), name='list'),
]
