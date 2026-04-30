# waste/models.py

from django.db import models

from core.models import CoreModel

# Create your models here.

class WasteFractionType(CoreModel):
    """Kategoria frakcji – np. Zmieszane, Papier, Bio."""
    name = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='Nazwa frakcji'
    )
    code = models.IntegerField(
        unique=True,
        verbose_name='Kod frakcji'
    )
    active = models.BooleanField(default=True, verbose_name='Aktywny')
        
    class Meta:
        verbose_name = 'Kategoria frakcji'
        verbose_name_plural = 'Kategorie frakcji'
        ordering = ['code']

    def __str__(self) -> str:
        return f"{self.code} – {self.name}"
    
class WasteFraction(CoreModel):
    """Słownik frakcji odpadów."""
    fraction_type = models.ForeignKey(
        WasteFractionType,
        on_delete=models.PROTECT,
        related_name='fractions',
        verbose_name='Rodzaj frakcji'
    )
    capacity = models.IntegerField(
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
        ordering = ['fraction_type__code', 'capacity']
    
    def __str__(self) -> str:
        return f"{self.fraction_type.name} ({self.capacity} {self.unit})"