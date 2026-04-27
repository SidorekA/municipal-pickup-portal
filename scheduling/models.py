# scheduling/models.py
from __future__ import annotations

from django.db import models

from core.models import TimeStampedModel


class PickupSchedule(TimeStampedModel):
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.CASCADE,
        related_name="pickup_schedules",
    )
    fraction = models.ForeignKey(
        "locations.WasteFraction",
        on_delete=models.PROTECT,
        related_name="pickup_schedules",
    )
    weekday = models.PositiveSmallIntegerField()  # 0=pon ... 6=nd
    typical_pickup_time = models.TimeField()
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["location", "fraction", "weekday"]),
        ]

    def __str__(self) -> str:
        return f"{self.location} / {self.fraction} / {self.weekday}"