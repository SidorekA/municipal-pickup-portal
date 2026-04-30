# locations/admin.py
from django.contrib import admin
from .models import MPKNumber, Location, WasteFractionType, WasteFraction, LocationWasteBin


class LocationInline(admin.TabularInline):
    model = Location
    extra = 1
    fields = ['obj_name', 'org_unit_name', 'localization', 'active']


class WasteFractionInline(admin.TabularInline):
    model = WasteFraction
    extra = 1
    fields = ['capacity', 'unit', 'active']


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


@admin.register(WasteFractionType)
class WasteFractionTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'active']
    list_filter = ['active']
    search_fields = ['name', 'code']
    inlines = [WasteFractionInline]


# @admin.register(WasteFraction)
# class WasteFractionAdmin(admin.ModelAdmin):
#     list_display = ['fraction_type', 'capacity', 'unit', 'active']
#     list_filter = ['active', 'fraction_type']
#     search_fields = ['fraction_type__name']
#     ordering = ['fraction_type__code', 'capacity']


# @admin.register(LocationWasteBin)
# class LocationWasteBinAdmin(admin.ModelAdmin):
#     list_display = ['location', 'waste_fraction', 'quantity']
#     search_fields = ['location__obj_name', 'waste_fraction__fraction_type__name']
#     ordering = ['location', 'waste_fraction']