# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile

User = get_user_model()


class UserBasicForm(forms.ModelForm):
    """Edycja podstawowych danych konta (imię, nazwisko, email)."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Imię',
            'last_name':  'Nazwisko',
            'email':      'Adres e-mail',
        }


class UserProfileForm(forms.ModelForm):
    """Edycja danych profilu (telefon, jednostka)."""
    class Meta:
        model = UserProfile
        fields = ['phone', 'department_short', 'department_name']
        widgets = {
            'phone':           forms.TextInput(attrs={'class': 'form-control'}),
            'department_short': forms.TextInput(attrs={'class': 'form-control'}),
            'department_name':  forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'phone':            'Numer telefonu',
            'department_short': 'Skrót jednostki',
            'department_name':  'Nazwa jednostki',
        }


class StyledPasswordChangeForm(PasswordChangeForm):
    """Zmiana hasła z Bootstrap-owym stylem."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['old_password'].label     = 'Aktualne hasło'
        self.fields['new_password1'].label    = 'Nowe hasło'
        self.fields['new_password2'].label    = 'Powtórz nowe hasło'