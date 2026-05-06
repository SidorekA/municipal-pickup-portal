# pickups/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.tasks import wyslij_zgloszenie_email
from .forms import PickupForm, PickupWasteBinFormSet

@login_required
def create_pickup(request):
    location_id = request.POST.get('location') if request.method == 'POST' else None

    if request.method == 'POST':
        form = PickupForm(request.POST, user=request.user, location_id=location_id)
        
        if form.is_valid():
            pickup = form.save(commit=False)
            pickup.reporter = request.user
            formset = PickupWasteBinFormSet(request.POST, instance=pickup)
            
            if formset.is_valid():
                pickup.save()
                formset.save()
                wyslij_zgloszenie_email.delay(pickup.id)
                
                messages.success(request, f"Zgłoszenie {pickup.pickup_number} zostało utworzone i przekazane do wysyłki.")
                return redirect('pickups:success')
            else:
                messages.error(request, "Popraw błędy w sekcji pojemników.")
        else:
            formset = PickupWasteBinFormSet(request.POST)
            messages.error(request, "Popraw błędy w formularzu głównym.")

    else:
        form = PickupForm(user=request.user)
        formset = PickupWasteBinFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'pickups/pickup_form.html', context)

def pickup_success(request):
    """Wyświetla stronę z podziękowaniem po dodaniu zgłoszenia."""
    return render(request, 'pickups/success.html')