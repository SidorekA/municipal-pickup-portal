# waste/admin.py

from django.contrib import admin
from .models import WasteFractionType, WasteFraction
# Register your models here.

class WasteFractionInline(admin.TabularInline):
    model = WasteFraction
    extra = 1
    fields = ['capacity', 'unit', 'active']

@admin.register(WasteFractionType)
class WasteFractionTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'active']
    list_filter = ['active']
    search_fields = ['name', 'code']
    inlines = [WasteFractionInline]