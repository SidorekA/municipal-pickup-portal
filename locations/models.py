# locations/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class MPKNumber(TimeStampedModel):
    number = models.CharField(max_length=32, unique=True)  # np. "MPK-001"
    short_name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.number} ({self.short_name})"


class Location(TimeStampedModel):
    mpk_number = models.ForeignKey(
        MPKNumber,
        on_delete=models.PROTECT,
        related_name="locations",
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=16)
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coordinated_locations",
    )
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.name} / {self.city}"


class WasteFraction(TimeStampedModel):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32, unique=True)
    unit = models.CharField(max_length=16, default="kg")
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"