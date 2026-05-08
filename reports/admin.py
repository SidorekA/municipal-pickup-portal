#reports/admin.py

from django.contrib import admin
from .models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin

@admin.register(SummaryCollectionSchedule)
class SummaryCollectionScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'mpk_number', 
        'year', 
        'month', 
        'waste_fraction', 
        'quantity', 
        'date_summary', 
        'imported_at'
    )
    list_filter = ('year', 'month', 'mpk_number', 'waste_fraction')
    search_fields = ('mpk_number__mpk_number', 'waste_fraction__fraction_type__name')
    readonly_fields = ('imported_at', 'imported_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.imported_by = request.user
        super().save_model(request, obj, form, change)


class MonthlyConfirmationBinInline(admin.TabularInline):
    model = MonthlyConfirmationBin
    extra = 0  
    

@admin.register(MonthlyConfirmation)
class MonthlyConfirmationAdmin(admin.ModelAdmin):
    list_display = (
        'mpk_number', 
        'month', 
        'status', 
        'approved_by'
    )
    
    list_filter = ('status', 'month', 'mpk_number') 
    
    search_fields = (
        'mpk_number__mpk_number', 
    )
    
    readonly_fields = (
        'approved_at', 
        'approved_by',
        'created_by',
        'updated_by',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('mpk_number', 'month', 'status', 'created_by', 'created_at', 'updated_by', 'updated_at'), 
        }),
        ('Zatwierdzenie (Admin)', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MonthlyConfirmationBinInline]


@admin.register(MonthlyConfirmationBin)
class MonthlyConfirmationBinAdmin(admin.ModelAdmin):
    list_display = ('confirmation', 'waste_fraction', 'confirmed_quantity', 'note')
    list_filter = ('waste_fraction',)
    search_fields = ('confirmation__mpk_number__mpk_number', 'waste_fraction__fraction_type__name')