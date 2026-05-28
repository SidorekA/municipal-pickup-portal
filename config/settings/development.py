from .base import *

DEBUG = True
ALLOWED_HOSTS = ["testserver",
    "frog03-20514.wykr.es",
    "127.0.0.1",
    "localhost",
]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True