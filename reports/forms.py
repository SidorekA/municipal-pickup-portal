#reports/forms.py
from django import forms
from locations.models import MPKNumber
from users.models import Permission
import datetime

class ReportFilterForm(forms.Form):
    # DOKLEJAMY PUSTĄ OPCJĘ NA POCZĄTEK LISTY MIESIĘCY I LAT
    MONTH_CHOICES = [('', 'Wszystkie')] + [(i, f"{i:02d}") for i in range(1, 13)]
    
    current_year = datetime.date.today().year
    YEAR_CHOICES = [('', 'Wszystkie')] + [(year, str(year)) for year in range(current_year - 2, current_year + 2)]

    mpk = forms.ChoiceField(
        required=False,
        label="Numer MPK",
        widget=forms.Select(attrs={'class': 'form-select report-filter__select', 'onchange': 'this.form.submit()'})
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES, 
        required=False, 
        label="Miesiąc",
        widget=forms.Select(attrs={'class': 'form-select report-filter__select', 'onchange': 'this.form.submit()'})
    )
    year = forms.ChoiceField(
        choices=YEAR_CHOICES, 
        required=False, 
        label="Rok",
        widget=forms.Select(attrs={'class': 'form-select report-filter__select', 'onchange': 'this.form.submit()'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        mpk_choices = [('', 'Wszystkie przypisane')]
        
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
        
        self.fields['mpk'].choices = mpk_choices