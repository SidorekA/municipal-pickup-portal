# locations/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import CoreModel


class MPKNumber(CoreModel):
    """Słownik numerów MPK (miejsc powstawania kosztów)."""
    mpk_number = models.CharField(max_length=32)
    active = models.BooleanField(default=True, 
                                 verbose_name='Aktywny'
                                )
    class Meta:
        verbose_name = 'Numer MPK'
        verbose_name_plural = 'Numery MPK'
        ordering = ['mpk_number']
        
        constraints = [
            models.UniqueConstraint(
                fields=["mpk_number"],
                name="uniq_mpk_number"
            )
        ]

    def __str__(self) -> str:
        return f"{self.mpk_number}"


class Location(CoreModel):
    """Lokalizacja powiązana z numerem MPK."""
    mpk_number = models.ForeignKey(
        MPKNumber,
        on_delete=models.PROTECT,
        related_name="locations",
        verbose_name='Lokalizacja',
    )
    obj_name = models.CharField(max_length=200, 
                                blank=False, 
                                verbose_name='Nazwa obiektu'
                                )
    org_unit_name = models.CharField(max_length=20, 
                                     blank=False, 
                                     verbose_name='Nazwa jednostki organizacyjnej'
                                     )
    localization = models.CharField(max_length=128, 
                                    blank=False, 
                                    verbose_name='Lokalizacja'
                                    )
    active = models.BooleanField(default=True, 
                                 verbose_name='Aktywny'
                                 )
    
    class Meta:
        verbose_name = 'Lokalizacja'
        verbose_name_plural = 'Lokalizacje'
        ordering = ['mpk_number', 'obj_name']

    def __str__(self) -> str:
        return f"{self.obj_name} / {self.localization}"

class WasteFraction(CoreModel):
    """Słownik frakcji odpadów."""
    name = models.CharField(max_length=40, 
                            verbose_name='Nazwa frakcji'
                            )
    code = models.CharField(max_length=15,  
                            verbose_name='Kod frakcji'
                            )
    capacity = models.IntegerField(
        max_digits=10, 
        null=False,
        verbose_name='Pojemność'
    )
    unit = models.CharField(max_length=5, 
                            default="l", 
                            verbose_name='Jednostka'
                            )
    active = models.BooleanField(default=True, 
                                 verbose_name='Aktywny'
                                 )
    
    class Meta:
        verbose_name = 'Frakcja odpadów'
        verbose_name_plural = 'Frakcje odpadów'
        ordering = ['code', 'capacity']
    
    def __str__(self) -> str:
        return f"{self.name} ({self.capacity} {self.unit})"
    

class LocationWasteBin(CoreModel):
    """Pojemniki przypisane do lokalizacji (jakie frakcje i ile pojemników)."""
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE,
        related_name='waste_bins', 
        verbose_name='Lokalizacja'
    )
    waste_fraction = models.ForeignKey(
        WasteFraction, 
        on_delete=models.PROTECT,
        related_name='location_bins', 
        verbose_name='Frakcja'
    )
    quantity = models.PositiveIntegerField(default=1, 
                                           verbose_name='Ilość pojemników'
                                           )

    class Meta:
        verbose_name = 'Pojemnik lokalizacji'
        verbose_name_plural = 'Pojemniki lokalizacji'
        ordering = ['location', 'waste_fraction']
        
        constraints = [
            models.UniqueConstraint(
                fields=["location", "waste_fraction"],
                name="uniq_location_waste_fraction"
            )
        ]

    def __str__(self) -> str:
        return f"{self.location} – {self.quantity} × {self.waste_fraction}"
