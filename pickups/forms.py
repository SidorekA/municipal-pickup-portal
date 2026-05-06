# pickups/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Pickup, PickupWasteBin
from locations.models import LocationContact, Location

class PickupForm(forms.ModelForm):
    class Meta:
        model = Pickup
        fields = ['mpk_number', 'location', 'contact_phone', 'note']
        widgets = {
            'mpk_number': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'contact_phone': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.location_id = kwargs.pop('location_id', None)
        super().__init__(*args, **kwargs)

        phone_choices = [('', '--- Wybierz numer kontaktowy ---')]
        
        if self.user and hasattr(self.user, 'profile') and self.user.profile.phone:
            phone_choices.append((self.user.profile.phone, f"Mój numer: {self.user.profile.phone}"))

        if self.location_id:
            contacts = LocationContact.objects.filter(location_id=self.location_id, active=True)
            for contact in contacts:
                phone_choices.append((contact.phone_number, f"{contact.contact_name}: {contact.phone_number}"))

        self.fields['contact_phone'].widget.choices = phone_choices

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if not phone:
            raise forms.ValidationError("Musisz podać numer telefonu dla kierowcy.")
        return phone

PickupWasteBinFormSet = inlineformset_factory(
    parent_model=Pickup,
    model=PickupWasteBin,
    fields=['waste_fraction', 'quantity'],
    extra=1,  # Pokaż domyślnie 1 pusty wiersz do dodania frakcji
    can_delete=True,  # Pozwala użytkownikowi usuwać wiersze z formularza
    widgets={
        'waste_fraction': forms.Select(attrs={'class': 'form-select'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
    }
)