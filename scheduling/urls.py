from django.urls import path
from .views import CalendarView

app_name = 'scheduling'

urlpatterns = [
    path('', CalendarView.as_view(), name='calendar'),
    path('<int:year>/<int:month>/', CalendarView.as_view(), name='calendar_month'),
]
