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
        'locations.MpkNumber', on_delete=models.PROTECT,
        related_name='summaries', verbose_name='Numer MPK'
    )
    year = models.PositiveSmallIntegerField(verbose_name='Rok')
    month = models.PositiveSmallIntegerField(verbose_name='Miesiąc')
    waste_fraction = models.ForeignKey(
        'locations.WasteFraction', on_delete=models.PROTECT,
        related_name='summaries', verbose_name='Frakcja'
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Ilość'
    )
    date_summary = models.DateField(verbose_name='Data zestawienia')
    note = models.TextField(blank=True, default='', verbose_name='Uwagi')
    imported_at = models.DateTimeField(auto_now_add=True, verbose_name='Data importu')
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='imported_summaries', verbose_name='Zaimportował'
    )

    class Meta:
        db_table = 'summary_collection_schedule'
        verbose_name = 'Zestawienie odbioru'
        verbose_name_plural = 'Zestawienia odbiorów'
        ordering = ['-year', '-month', 'mpk_number']

    def __str__(self):
        return f'{self.mpk_number} {self.year}/{self.month:02d} – {self.waste_fraction.code}'

class MonthlyConfirmation(CoreModel):
    """Potwierdzenie miesięczne dla lokalizacji."""
    STATUS_CHOICES = [
        ('OCZEKUJE', 'Oczekuje'),
        ('POTWIERDZONE', 'Potwierdzone'),
        ('ZATWIERDZONE', 'Zatwierdzone'),
    ]
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="monthly_confirmations",
        verbose_name='Lokalizacja'
    )
    month = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='OCZEKUJE', verbose_name='Status')

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='confirmed_monthly', 
        verbose_name='Potwierdzający'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_monthly', 
        verbose_name='Zatwierdzający',
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, default='', verbose_name='Uwagi')

    class Meta:
        db_table = 'monthly_confirmations'
        verbose_name = 'Potwierdzenie miesięczne'
        verbose_name_plural = 'Potwierdzenia miesięczne'
        unique_together = [('location', 'month')]
        ordering = ['-month', 'location']

    def __str__(self):
        return f'{self.location} – {self.month.strftime("%Y/%m")} ({self.get_status_display()})'
    
class Cost(CoreModel):
    """Koszt za frakcję odpadów w danym okresie."""
    waste_fraction = models.ForeignKey(
        'locations.WasteFraction', on_delete=models.PROTECT,
        related_name='costs', verbose_name='Frakcja'
    )
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Koszt (PLN)')
    date_from = models.DateField(verbose_name='Obowiązuje od')
    date_to = models.DateField(null=True, blank=True, verbose_name='Obowiązuje do')
    note = models.TextField(blank=True, default='', verbose_name='Uwagi')

    class Meta:
        db_table = 'costs'
        verbose_name = 'Koszt frakcji'
        verbose_name_plural = 'Koszty frakcji'
        ordering = ['-date_from', 'waste_fraction']

    def __str__(self):
        return f'{self.waste_fraction.code} – {self.cost} PLN (od {self.date_from})'