from django.contrib import admin
from .models import SummaryCollectionSchedule, MonthlyConfirmation

@admin.register(SummaryCollectionSchedule)
class SummaryCollectionScheduleAdmin(admin.ModelAdmin):
    # Kolumny widoczne na liście
    list_display = (
        'mpk_number', 
        'year', 
        'month', 
        'waste_fraction', 
        'quantity', 
        'date_summary', 
        'imported_at'
    )
    
    # Filtry po prawej stronie
    list_filter = ('year', 'month', 'mpk_number', 'waste_fraction')
    
    # Pola wyszukiwania (używamy __ aby przeszukać pola w relacjach)
    search_fields = ('mpk_number__mpk_number', 'waste_fraction__fraction_type__name')
    
    # Pola tylko do odczytu
    readonly_fields = ('imported_at', 'imported_by')

    def save_model(self, request, obj, form, change):
        # Automatyczne przypisanie użytkownika podczas ręcznego dodawania w adminie
        if not obj.pk:
            obj.imported_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MonthlyConfirmation)
class MonthlyConfirmationAdmin(admin.ModelAdmin):
    list_display = (
        'location', 
        'month', 
        'status', 
        'confirmed_by', 
        'approved_by'
    )
    
    list_filter = ('status', 'month', 'location')
    
    search_fields = (
        'location__obj_name', 
        'location__localization'
    )
    
    readonly_fields = (
        'confirmed_at', 
        'approved_at', 
        'confirmed_by', 
        'approved_by'
    )
    
    # Grupowanie pól w formularzu edycji dla lepszej przejrzystości
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('location', 'month', 'status')
        }),
        ('Potwierdzenie (Użytkownik)', {
            'fields': ('confirmed_by', 'confirmed_at'),
            'classes': ('collapse',)
        }),
        ('Zatwierdzenie (Admin)', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )