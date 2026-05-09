# reports/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import CoreModel

class SummaryCollectionSchedule(CoreModel):
    """
    Zestawienie odbiorów od dostawcy.
    Uzupełniane przez import pliku Excel od firmy odbierającej.
    """
    mpk_number = models.ForeignKey(
        'locations.MPKNumber', on_delete=models.PROTECT,
        related_name='summaries', verbose_name='Numer MPK'
    )
    year = models.PositiveSmallIntegerField(verbose_name='Rok')
    month = models.PositiveSmallIntegerField(verbose_name='Miesiąc')
    waste_fraction = models.ForeignKey(
        'waste.WasteFraction', on_delete=models.PROTECT,
        related_name='summaries', verbose_name='Frakcja'
    )
    quantity = models.IntegerField(
        verbose_name='Ilość'
    )
    date_summary = models.DateField(verbose_name='Data zestawienia')
    imported_at = models.DateTimeField(auto_now_add=True, verbose_name='Data importu')
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='imported_summaries', verbose_name='Zaimportował'
    )

    class Meta:
        verbose_name = 'Zestawienie odbioru'
        verbose_name_plural = 'Zestawienia odbiorów'
        ordering = ['-year', '-month', 'mpk_number']

    def __str__(self):
        return f'{self.mpk_number} {self.year}/{self.month:02d} – {self.waste_fraction.fraction_type.name}'

class MonthlyConfirmation(CoreModel):
    """Nagłówek potwierdzenia miesiąca dla MPK."""
    STATUS_CHOICES = [
        ('OCZEKUJE', 'Oczekuje'),
        ('POTWIERDZONE', 'Potwierdzone'),
        ('ZATWIERDZONE', 'Zatwierdzone'),
        ('KONFLIKT', 'Konflikt (Rozbieżności)'),
    ]
    
    mpk_number = models.ForeignKey('locations.MPKNumber', on_delete=models.PROTECT, related_name='confirmations')
    month = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='OCZEKUJE')
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='approved_monthly',
        verbose_name='Zatwierdzający'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Data zatwierdzenia')
    
    class Meta:
        unique_together = [('mpk_number', 'month')]
    
class MonthlyConfirmationBin(CoreModel):
    """Tylko faktycznie potwierdzona ilość, jeśli różni się od zgłoszeń/importów."""
    confirmation = models.ForeignKey(MonthlyConfirmation, on_delete=models.CASCADE, related_name='bins')
    waste_fraction = models.ForeignKey('waste.WasteFraction', on_delete=models.PROTECT)
    confirmed_quantity = models.IntegerField(verbose_name='Potwierdzona ilość')
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = [('confirmation', 'waste_fraction')]