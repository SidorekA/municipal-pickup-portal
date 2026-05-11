import importlib.util

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Narzędzia deweloperskie — ładuj tylko jeśli zainstalowane
if importlib.util.find_spec('silk') is not None:
    INSTALLED_APPS += ['silk']  # noqa: F405
    MIDDLEWARE = ['silk.middleware.SilkyMiddleware'] + MIDDLEWARE  # noqa: F405

if importlib.util.find_spec('debug_toolbar') is not None:
    INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE  # noqa: F405
    INTERNAL_IPS = ['127.0.0.1']