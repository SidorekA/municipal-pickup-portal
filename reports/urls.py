from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('podsumowanie/', views.monthly_summary_view, name='monthly_summary'),
    path('weryfikacja/', views.verification_view, name='verification'),
]
