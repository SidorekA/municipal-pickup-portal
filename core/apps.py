
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        from django.contrib import admin
        from auditlog.registry import auditlog
        from django.apps import apps
        from core.models import CoreModel, DataTransferLog
        admin.site.site_header = 'System Zarządzania Odpadami – Admin'
        admin.site.site_title = 'Odpady Admin'
        admin.site.index_title = 'Panel administracyjny'
        
        for model in apps.get_models():
            if issubclass(model, CoreModel) and model not in [CoreModel, DataTransferLog]:
                try:
                    auditlog.register(model, exclude_fields=['updated_at', 'updated_by'])
                except Exception:
                    pass