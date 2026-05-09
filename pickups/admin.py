
# pickups/admin.py
from django.contrib import admin
from .models import Pickup, PickupWasteBin


class PickupWasteBinInline(admin.TabularInline):
    model = PickupWasteBin
    extra = 1


@admin.register(Pickup)
class PickupAdmin(admin.ModelAdmin):
    list_display = ['pickup_number', 'location', 'mpk_number', 'reporter', 'status', 'reported_at']
    list_filter = ['status', 'mpk_number']
    search_fields = ['pickup_number', 'location__obj_name', 'reporter__username']
    ordering = ['-reported_at']
    readonly_fields = ['pickup_number', 'reported_at']
    inlines = [PickupWasteBinInline]
