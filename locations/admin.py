# locations/admin.py
from django.contrib import admin
from .models import MPKNumber, Location,LocationWasteBin

class LocationInline(admin.TabularInline):
    model = Location
    extra = 1
    fields = ['obj_name', 'org_unit_name', 'localization', 'active']

class LocationWasteBinInline(admin.TabularInline):
    model = LocationWasteBin
    extra = 1
    fields = ['waste_fraction', 'quantity']


@admin.register(MPKNumber)
class MPKNumberAdmin(admin.ModelAdmin):
    list_display = ['mpk_number', 'active']
    list_filter = ['active']
    search_fields = ['mpk_number']
    inlines = [LocationInline]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['obj_name', 'mpk_number', 'org_unit_name', 'localization', 'active']
    list_filter = ['active', 'mpk_number']
    search_fields = ['obj_name', 'localization', 'mpk_number__mpk_number']
    ordering = ['mpk_number', 'obj_name']
    inlines = [LocationWasteBinInline]
