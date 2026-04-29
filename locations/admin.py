# locations/admin.py
from django.contrib import admin
# from .models import Location, MPKNumber, WasteFraction

# @admin.register(MPKNumber)
# class MPKNumberAdmin(admin.ModelAdmin):
#     list_display = ("number", "short_name", "active", "created_at", "updated_at")
#     list_filter = ("active",)
#     search_fields = ("number", "short_name")

# @admin.register(Location)
# class LocationAdmin(admin.ModelAdmin):
#     list_display = ("name", "city", "postal_code", "mpk_number", "coordinator", "active")
#     list_filter = ("active", "city", "mpk_number")
#     search_fields = ("name", "city", "postal_code", "mpk_number__number")

# @admin.register(WasteFraction)
# class WasteFractionAdmin(admin.ModelAdmin):
#     list_display = ("name", "code", "unit", "active")
#     list_filter = ("active", "unit")
#     search_fields = ("name", "code")