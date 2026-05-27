# pickups/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from users.models import Permission
# from .tasks import wyslij_zgloszenie_email
from .tasks import wyslij_email_sync

from pickups.models import Pickup, PickupWasteBin
from .forms import PickupForm, PickupFilterForm
from django.http import JsonResponse
from locations.models import Location, LocationContact, LocationWasteBin
from scheduling.services import get_next_pickup_date
import logging
logger = logging.getLogger(__name__)

@login_required
def create_pickup(request):
    location_id = request.POST.get('location') if request.method == 'POST' else None

    if request.method == 'POST':
        form = PickupForm(request.POST, user=request.user, location_id=location_id)
        
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.reporter = request.user
            pickup.save()
            
            waste_bins = []
            for key, value in request.POST.items():
                if key.startswith('bin_') and value.isdigit() and int(value) > 0:
                    fraction_id = int(key.split('_')[1])
                    ilosc = int(value)
                    
                    waste_bins.append(PickupWasteBin(
                        pickup=pickup,
                        waste_fraction_id=fraction_id,
                        quantity=ilosc
                    ))

            if waste_bins:
                PickupWasteBin.objects.bulk_create(waste_bins)
                kosze_dodane = True
            else:
                kosze_dodane = False

            if not kosze_dodane:
                pickup.delete()
                
                messages.error(request, "Musisz wybrać ilość przynajmniej jednego pojemnika do odbioru!")
                return render(request, 'pickups/pickup_form.html', {'form': form})

            # wyslij_zgloszenie_email.delay(pickup.id)
            try:
                wyslij_email_sync(pickup.id)
            except Exception as e:
                logger.warning(f"Email nie został wysłany: {e}")
            messages.success(request, f"Zgłoszenie {pickup.pickup_number} zostało utworzone!")
            return redirect('pickups:pickup_success')
        else:
            messages.error(request, "Popraw błędy w formularzu głównym.")
    else:
        form = PickupForm(user=request.user)

    return render(request, 'pickups/pickup_form.html', {'form': form})

def pickup_success(request):
    """Wyświetla stronę z podziękowaniem po dodaniu zgłoszenia."""
    return render(request, 'pickups/pickup_success.html')

def api_get_pickup_dates(request, location_id):
    """
    Zwraca przewidywane daty odbioru dla frakcji przypisanych
    do danej lokalizacji, obliczone na podstawie harmonogramu.
    Używane przez dynamic_bins.js do wyświetlenia daty przed submitem.
    """
    from django.utils import timezone
    from scheduling.services import get_next_pickup_date

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Nie zalogowano'}, status=403)

    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        return JsonResponse({'error': 'Lokalizacja nie istnieje'}, status=404)

    has_permission = request.user.is_superuser or Permission.objects.filter(
        user=request.user,
        mpk_number=location.mpk_number,
        active=True
    ).exists()

    if not has_permission:
        return JsonResponse({'error': 'Brak uprawnień do tej lokalizacji'}, status=403)

    bins = LocationWasteBin.objects.filter(
        location_id=location_id
    ).select_related(
        'waste_fraction__fraction_type'
    ).prefetch_related(
        'waste_fraction__fraction_type__schedules'
    )

    now = timezone.now()
    data = []
    for b in bins:
        planned = get_next_pickup_date(
            fraction_type=b.waste_fraction.fraction_type,
            submitted_at=now
        )
        data.append({
            'fraction_id': b.waste_fraction.id,
            'planned_date': planned.strftime('%d.%m.%Y (%A)') if planned else None,
        })

    return JsonResponse({'dates': data})

def api_get_location_bins(request, location_id):
    """Zwraca listę przypisanych pojemników dla danej lokalizacji w formacie JSON."""
    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        return JsonResponse({'error': 'Lokalizacja nie istnieje'}, status=404)

    has_permission = False
    if request.user.is_authenticated:
        has_permission = request.user.is_superuser or Permission.objects.filter(
            user=request.user,
            mpk_number=location.mpk_number,
            active=True
        ).exists()

    if not has_permission:
        return JsonResponse({'error': 'Brak uprawnień do tej lokalizacji'}, status=403)

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
    
    has_permission = False
    if request.user.is_authenticated:
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
        'waste_bins__waste_fraction__fraction_type__schedules'
        )
    
    if not request.user.is_superuser:
        allowed_mpk_ids = Permission.objects.filter(
            user=request.user, 
            active=True
        ).values_list('mpk_number_id', flat=True)
        
        queryset = queryset.filter(mpk_number_id__in=allowed_mpk_ids)

    form = PickupFilterForm(request.GET or None, user=request.user)
    if form.is_valid():
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        mpk = form.cleaned_data.get('mpk')
        location = form.cleaned_data.get('location')

        if date_from:
            queryset = queryset.filter(reported_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(reported_at__date__lte=date_to)
        if mpk:
            queryset = queryset.filter(mpk_number_id=mpk)
        if location:
            queryset = queryset.filter(location_id=location)

        status = request.GET.get('status', '').strip()
        if status and status in dict(Pickup.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
    
    pickups = list(queryset.order_by('-created_at'))

    for pickup in pickups:
        for bin in pickup.waste_bins.all():
            bin.planned_date = get_next_pickup_date(
                fraction_type=bin.waste_fraction.fraction_type,
                submitted_at=pickup.reported_at
            )
    
    return render(request, 'pickups/pickup_list.html', {'pickups': pickups, 'form': form})