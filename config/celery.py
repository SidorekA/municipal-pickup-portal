# config/celery.py
import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.development",
)

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-overdue-confirmations-daily': {
        'task': 'notifications.tasks.check_overdue_confirmations',
        'schedule': crontab(hour=8, minute=0),  # Codziennie o 8:00
    },
}