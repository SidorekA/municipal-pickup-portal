# pickups/forms.py
from django import forms

from users.models import Permission
from .models import Pickup
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
        
        self.fields['mpk_number'].empty_label = "Wybierz nr MPK"
        self.fields['location'].empty_label = "Wybierz lokalizację"

        if self.user and not self.user.is_superuser:
            allowed_mpk_ids = Permission.objects.filter(
                user=self.user, 
                active=True
            ).values_list('mpk_number_id', flat=True)
            
            self.fields['mpk_number'].queryset = self.fields['mpk_number'].queryset.filter(
                id__in=allowed_mpk_ids
            )
            
        if self.fields['mpk_number'].queryset.count() == 1:
            self.fields['mpk_number'].initial = self.fields['mpk_number'].queryset.first()
            
        self.fields['location'].queryset = self.fields['location'].queryset.none()
        if 'mpk_number' in self.data:
            try:
                mpk_id = int(self.data.get('mpk_number'))
                self.fields['location'].queryset = Location.objects.filter(mpk_number_id=mpk_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.mpk_number:
            self.fields['location'].queryset = self.instance.mpk_number.location_set.all()
            
        phone_choices = [('', 'Wybierz numer kontaktowy')]
        
        if self.user and hasattr(self.user, 'profile') and self.user.profile.phone:
            phone_choices.append((self.user.profile.phone, f"Mój numer: {self.user.profile.phone}"))

        loc_id = self.data.get('location') or self.location_id
        
        if loc_id:
            contacts = LocationContact.objects.filter(location_id=loc_id, active=True)
            for contact in contacts:
                phone_choices.append((contact.phone_number, f"{contact.contact_name}: {contact.phone_number}"))

        self.fields['contact_phone'].widget.choices = phone_choices

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if not phone:
            raise forms.ValidationError("Musisz podać numer telefonu dla kierowcy.")
        return phone
class PickupFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label="Data od",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control report-filter__select', 'onchange': 'this.form.submit()'})
    )
    date_to = forms.DateField(
        required=False,
        label="Data do",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control report-filter__select', 'onchange': 'this.form.submit()'})
    )
    mpk = forms.ChoiceField(
        required=False,
        label="Numer MPK",
        widget=forms.Select(attrs={'class': 'form-select report-filter__select', 'onchange': 'this.form.submit()'})
    )
    location = forms.ChoiceField(
        required=False,
        label="Lokalizacja",
        widget=forms.Select(attrs={'class': 'form-select report-filter__select', 'onchange': 'this.form.submit()'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        mpk_choices = [('', 'Wszystkie przypisane')]
        location_choices = [('', 'Wszystkie')]

        from locations.models import MPKNumber, Location

        if self.user:
            if self.user.is_superuser:
                mpks = MPKNumber.objects.all().order_by('mpk_number')
            else:
                allowed_mpk_ids = Permission.objects.filter(
                    user=self.user, active=True
                ).values_list('mpk_number_id', flat=True)
                mpks = MPKNumber.objects.filter(id__in=allowed_mpk_ids).order_by('mpk_number')

            for mpk in mpks:
                mpk_choices.append((str(mpk.id), str(mpk.mpk_number)))

            selected_mpk = self.data.get('mpk') or self.initial.get('mpk')

            if selected_mpk:
                locations = Location.objects.filter(mpk_number_id=selected_mpk).order_by('obj_name')
                for loc in locations:
                    location_choices.append((str(loc.id), f"{loc.localization} - {loc.obj_name}"))
            else:
                 # If no MPK selected, we can either show no locations or all locations the user has access to.
                 # Let's show all locations they have access to.
                 if self.user.is_superuser:
                     locations = Location.objects.all().order_by('obj_name')
                 else:
                     locations = Location.objects.filter(mpk_number_id__in=mpks.values_list('id', flat=True)).order_by('obj_name')
                 for loc in locations:
                     location_choices.append((str(loc.id), f"{loc.localization} - {loc.obj_name}"))

        self.fields['mpk'].choices = mpk_choices
        self.fields['location'].choices = location_choices
