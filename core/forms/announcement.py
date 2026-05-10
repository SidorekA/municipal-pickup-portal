from django import forms
from notifications.models import Notification

class GlobalAnnouncementForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['message', 'alert_type']
