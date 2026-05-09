# waste/admin.py

from django.contrib import admin
from .models import WasteCost, WasteFractionType, WasteFraction
# Register your models here.

class WasteFractionInline(admin.TabularInline):
    model = WasteFraction
    extra = 1
    fields = ['capacity', 'unit', 'active']

class WasteCostInline(admin.TabularInline):
    model = WasteCost
    extra = 1
    fields = ['cost', 'date_from', 'date_to']

@admin.register(WasteFractionType)
class WasteFractionTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'active']
    list_filter = ['active']
    search_fields = ['name', 'code']
    inlines = [WasteFractionInline]

@admin.register(WasteFraction)
class WasteFractionAdmin(admin.ModelAdmin):
    list_display = ['fraction_type', 'capacity', 'unit', 'active']
    list_filter = ['active']
    search_fields = ['fraction_type', 'capacity']
    inlines = [WasteCostInline]
