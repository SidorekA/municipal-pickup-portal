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
    obj_name = models.CharField(max_length=255)
    org_unit_name = models.TextField()
    localization = models.CharField(max_length=128)
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
        return f"{self.obj_name} / {self.localization}"


class WasteFraction(TimeStampedModel):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32, unique=True)
    unit = models.CharField(max_length=16, default="szt.")
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
    

class ContainerType(TimeStampedModel):
    capacity_liters = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=64)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.capacity_liters} L)"


class LocationContainer(TimeStampedModel):
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.CASCADE,
        related_name="containers",
    )
    container_type = models.ForeignKey(
        ContainerType,
        on_delete=models.PROTECT,
        related_name="location_containers",
    )
    count = models.PositiveIntegerField()

    class Meta:
        unique_together = ("location", "container_type")

    def __str__(self) -> str:
        return f"{self.location} – {self.count} × {self.container_type}"
