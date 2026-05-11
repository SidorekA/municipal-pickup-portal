# config/celery.py
import os

from celery import Celery
from celery.schedules import crontab

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    raise RuntimeError(
        "Zmienna środowiskowa DJANGO_SETTINGS_MODULE nie jest ustawiona. "
        "Ustaw ją przed uruchomieniem: "
        "export DJANGO_SETTINGS_MODULE=config.settings.development"
    )

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-overdue-confirmations-daily': {
        'task': 'notifications.tasks.check_overdue_confirmations',
        'schedule': crontab(hour=8, minute=0),  # Codziennie o 8:00
    },
}