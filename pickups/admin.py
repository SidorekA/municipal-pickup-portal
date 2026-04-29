# requests/admin.py
from django.contrib import admin
# from .models import Request, RequestLog

# class RequestLogInline(admin.TabularInline):
#     model = RequestLog
#     extra = 0
#     readonly_fields = ("created_at",)

# @admin.register(Request)
# class RequestAdmin(admin.ModelAdmin):
#     list_display = ("request_number", "location", "status", "reporter", "reported_at", "planned_pickup_date")
#     list_filter = ("status", "location__mpk_number")
#     search_fields = ("request_number", "location__name", "reporter__username")
#     inlines = [RequestLogInline]

# @admin.register(RequestLog)
# class RequestLogAdmin(admin.ModelAdmin):
#     list_display = ("request", "status", "user", "created_at")
#     list_filter = ("status",)
#     search_fields = ("request__request_number", "user__username")
