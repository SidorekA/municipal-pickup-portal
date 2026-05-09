from django.contrib import admin
from .models import Notification, NotificationSetting

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_short', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')

    def message_short(self, obj):
        return obj.message[:50]
    message_short.short_description = 'Wiadomość'

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'reminder_threshold_days')

    def has_add_permission(self, request):
        """Prevent adding multiple instances since it's a singleton."""
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the singleton instance."""
        return False
