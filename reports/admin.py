# reports/admin.py
from django.contrib import admin
# from .models import CollectionReport, MonthlyConfirmation

# @admin.register(CollectionReport)
# class CollectionReportAdmin(admin.ModelAdmin):
#     list_display = ("location", "pickup_date", "collector_company", "reference_document", "request", "entered_by")
#     list_filter = ("pickup_date", "location__mpk_number")
#     search_fields = ("location__name", "reference_document", "collector_company", "request__request_number")

# @admin.register(MonthlyConfirmation)
# class MonthlyConfirmationAdmin(admin.ModelAdmin):
#     list_display = ("location", "month", "status", "confirmer", "approver", "created_at")
#     list_filter = ("status", "month", "location__mpk_number")
#     search_fields = ("location__name",)
