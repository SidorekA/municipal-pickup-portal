# pickups/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from users.models import Permission
from .tasks import wyslij_zgloszenie_email
from pickups.models import Pickup, PickupWasteBin
from .forms import PickupForm
from django.http import JsonResponse
from locations.models import Location, LocationContact, LocationWasteBin
from scheduling.services import get_next_pickup_date

@login_required
def create_pickup(request):
    location_id = request.POST.get('location') if request.method == 'POST' else None

    if request.method == 'POST':
        form = PickupForm(request.POST, user=request.user, location_id=location_id)
        
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.reporter = request.user
            pickup.save()
            
            kosze_dodane = False
            for key, value in request.POST.items():
                if key.startswith('bin_') and value.isdigit() and int(value) > 0:
                    fraction_id = int(key.split('_')[1])
                    ilosc = int(value)
                    
                    PickupWasteBin.objects.create(
                        pickup=pickup,
                        waste_fraction_id=fraction_id,
                        quantity=ilosc
                    )
                    kosze_dodane = True
            if not kosze_dodane:
                pickup.delete()
                
                messages.error(request, "Musisz wybrać ilość przynajmniej jednego pojemnika do odbioru!")
                return render(request, 'pickups/pickup_form.html', {'form': form})

            wyslij_zgloszenie_email.delay(pickup.id)
            messages.success(request, f"Zgłoszenie {pickup.pickup_number} zostało utworzone!")
            return redirect('pickups:success')
        else:
            messages.error(request, "Popraw błędy w formularzu głównym.")
    else:
        form = PickupForm(user=request.user)

    return render(request, 'pickups/pickup_form.html', {'form': form})

def pickup_success(request):
    """Wyświetla stronę z podziękowaniem po dodaniu zgłoszenia."""
    return render(request, 'pickups/success.html')

def api_get_location_bins(request, location_id):
    """Zwraca listę przypisanych pojemników dla danej lokalizacji w formacie JSON."""
    bins = LocationWasteBin.objects.filter(location_id=location_id).select_related('waste_fraction__fraction_type')
    
    data = []
    for b in bins:
        data.append({
            'fraction_id': b.waste_fraction.id,
            'name': b.waste_fraction.fraction_type.name,
            'capacity': b.waste_fraction.capacity,
            'max_quantity': b.quantity,
        })
    
    contacts = LocationContact.objects.filter(location_id=location_id, active=True)
    contacts_data = []
    for c in contacts:
        contacts_data.append({
            'phone': c.phone_number,
            'name': c.contact_name
        })
        
    return JsonResponse({'bins': data, 'contacts': contacts_data})

def api_get_mpk_locations(request, mpk_id):
    """Zwraca listę lokalizacji przypisanych do konkretnego MPK."""
    
    has_permission = request.user.is_superuser or Permission.objects.filter(
        user=request.user, 
        mpk_number_id=mpk_id, 
        active=True
    ).exists()
    
    if not has_permission:
        # Jeśli nie ma dostępu, zwracamy pustą listę lub błąd 403
        return JsonResponse({'locations': [], 'error': 'Brak uprawnień do tego MPK'}, status=403)
    
    locations = Location.objects.filter(mpk_number_id=mpk_id)
    
    data = []
    for loc in locations:
        data.append({
            'id': loc.id,
            'name': f"{loc.localization} - {loc.obj_name}"
        })
        
    return JsonResponse({'locations': data})

@login_required
def pickup_list(request):
    """Wyświetla panel ze zgłoszeniami przefiltrowanymi przez uprawnienia."""
    
    queryset = Pickup.objects.select_related('mpk_number', 'location', 'reporter').prefetch_related(
        'waste_bins__waste_fraction__fraction_type',
        'waste_bins__waste_fraction__fraction_type__schedules'
        )
    
    if not request.user.is_superuser:
        allowed_mpk_ids = Permission.objects.filter(
            user=request.user, 
            active=True
        ).values_list('mpk_number_id', flat=True)
        
        queryset = queryset.filter(mpk_number_id__in=allowed_mpk_ids)
    
    pickups = list(queryset)
    
    for pickup in pickups:
        first_bin = pickup.waste_bins.first()
        if first_bin:
            pickup.planned_date = get_next_pickup_date(
                first_bin.waste_fraction.fraction_type,
                submitted_at=pickup.reported_at
            )
        else:
            pickup.planned_date = None
    
    return render(request, 'pickups/pickup_list.html', {'pickups': pickups})