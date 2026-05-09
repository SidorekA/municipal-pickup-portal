# scheduling/admin.py
from django.contrib import admin
from .models import CollectionSchedule


@admin.register(CollectionSchedule)
class CollectionScheduleAdmin(admin.ModelAdmin):
    list_display = ['fraction_type', 'day_of_week_display', 'active']
    list_filter = ['day_of_week', 'active']
    search_fields = ['fraction_type__name']
    ordering = ['day_of_week']

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = 'Dzień tygodnia'