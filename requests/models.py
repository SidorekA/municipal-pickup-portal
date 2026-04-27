# requests/models.py
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Request(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "NEW", "NOWE"
        SENT = "SENT", "WYSŁANE"
        CONFIRMED = "CONFIRMED", "POTWIERDZONE"
        COMPLETED = "COMPLETED", "ZREALIZOWANE"
        REJECTED = "REJECTED", "ODRZUCONE"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_number = models.CharField(max_length=32, unique=True)  # ZGL-YYYY-0001
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.PROTECT,
        related_name="requests",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_requests",
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    planned_pickup_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    fractions = models.JSONField()  # lista frakcji z ilościami
    xlsx_file = models.FileField(upload_to="requests/%Y/%m/", null=True, blank=True)
    notes = models.TextField(blank=True)
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_requests",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.request_number


class RequestLog(models.Model):
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_logs",
    )
    status = models.CharField(max_length=16, choices=Request.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.request.request_number} -> {self.status}"