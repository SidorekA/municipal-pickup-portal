from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('podsumowanie/', views.monthly_summary_view, name='monthly_summary'),
    path('weryfikacja/', views.verification_view, name='verification'),
    path('approve/<int:pk>/', views.approve_confirmation, name='approve_confirmation'),
    path('import/', views.import_excel_view, name='import_excel'),
    path('edytuj-zestawienia/', views.edit_summaries_view, name='edit_summaries'),
    path('edytuj-zestawienia/aktualizuj/', views.update_summary_quantity, name='update_summary_quantity'),
    path('edytuj-zestawienia/eksport/', views.export_summaries_xlsx, name='export_summaries_xlsx'),
    path('koszty/', views.cost_summary_view, name='cost_summary'),
]
