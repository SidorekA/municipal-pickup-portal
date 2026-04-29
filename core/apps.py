from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        from django.contrib import admin
        admin.site.site_header = 'System Zarządzania Odpadami – Admin'
        admin.site.site_title = 'Odpady Admin'
        admin.site.index_title = 'Panel administracyjny'