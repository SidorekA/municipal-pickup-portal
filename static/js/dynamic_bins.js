document.addEventListener("DOMContentLoaded", function() {
    const mpkSelect = document.getElementById("id_mpk_number");
    const locationSelect = document.getElementById("id_location");
    const binsContainer = document.getElementById("visual-bins-container");
    const instruction = document.getElementById("bins-instruction");
    const phoneSelect = document.getElementById("id_contact_phone");

    if (!locationSelect || !binsContainer || !mpkSelect) return;

    let initialPhoneOptions = phoneSelect ? phoneSelect.innerHTML : '';

    const colorMap = {
        'zmieszane': 'secondary', // szary
        'makulatura': 'primary',  // niebieski
        'plastik': 'warning',     // żółty
        'szkło': 'success',       // zielony
        'bio': 'success',         // zielony (inny odcień)
    };

    function getBinColor(name) {
        const lowerName = name.toLowerCase();
        for (const [key, color] of Object.entries(colorMap)) {
            if (lowerName.includes(key)) return color;
        }
        return 'dark';
    }

    mpkSelect.addEventListener("change", function() {
        const mpkId = this.value;
        const prevLocation = locationSelect.getAttribute("data-selected");
        
        // preserveLocation logic removed since it was complicated by JS Event API limits.
        // Instead, we just check prevLocation and let the UI refresh. It happens very fast.
        locationSelect.innerHTML = '<option value="" class="text-muted">--- Wybierz lokalizację ---</option>';
        binsContainer.innerHTML = '';
        instruction.style.display = 'block';

        if (phoneSelect) phoneSelect.innerHTML = initialPhoneOptions;

        if (mpkId) {
            locationSelect.disabled = true; 
            fetch(`/zgloszenia/api/mpk/${mpkId}/lokalizacje/`)
                .then(response => response.json())
                .then(data => {
                    data.locations.forEach(loc => {
                        const option = document.createElement('option');
                        option.value = loc.id;
                        option.textContent = loc.name;
                        locationSelect.appendChild(option);
                    });
            
                    locationSelect.disabled = false; 

                    if (prevLocation) {
                        locationSelect.value = prevLocation;
                        // Trigger location change to load bins too if we just set it
                        locationSelect.dispatchEvent(new Event("change"));
                    }
                })
                .catch(error => {
                    console.error("Błąd pobierania lokalizacji:", error);
                    locationSelect.disabled = false;
                });
        }
    });

    locationSelect.addEventListener("change", function() {
        const locationId = this.value;
        binsContainer.innerHTML = '';

        if (!locationId) {
            instruction.style.display = 'block';
            return;
        }

        instruction.style.display = 'none';
        binsContainer.innerHTML = '<div class="text-center w-100 mt-4"><div class="spinner-border text-success"></div><p class="text-muted mt-2">Ładowanie pojemników...</p></div>';
        
        if (phoneSelect) phoneSelect.innerHTML = initialPhoneOptions;
        if (!locationId) {
            instruction.style.display = 'block';
            return;
        }

        fetch(`/zgloszenia/api/lokalizacja/${locationId}/pojemniki/`)
            .then(response => response.json())
            .then(data => {
                binsContainer.innerHTML = '';
                
                if (phoneSelect && data.contacts) {
                    data.contacts.forEach(contact => {
                        const option = document.createElement('option');
                        option.value = contact.phone;
                        option.textContent = `${contact.name}: ${contact.phone}`;
                        phoneSelect.appendChild(option);
                    });
                    phoneSelect.disabled = false;
                }

                if (data.bins.length === 0) {
                    binsContainer.innerHTML = '<div class="alert alert-warning w-100">Brak przypisanych pojemników dla tej lokalizacji!</div>';
                    return;
                }

                data.bins.forEach(bin => {
                    const color = getBinColor(bin.name);
                    let initialValue = 0;
                    if (window.PREVIOUS_POST_DATA && window.PREVIOUS_POST_DATA["bin_" + bin.fraction_id]) {
                        initialValue = window.PREVIOUS_POST_DATA["bin_" + bin.fraction_id];
                    }

                    const cardHtml = `
                        <div class="col-6 col-md-3">
                            <div class="card bin-card h-100 border border-${color} shadow-sm text-center">
                                <div class="card-body d-flex flex-column align-items-center">
                                    <i class="bi bi-trash3-fill bin-icon text-${color} mb-2"></i>
                                    <h6 class="card-title fw-bold mb-0">${bin.name}</h6>
                                    <p class="text-muted small mb-3">${bin.capacity} L</p>
                                    
                                    <div class="mt-auto w-100">
                                        <label class="small fw-bold mb-1">Do odbioru:</label>
                                        <input type="number" name="bin_${bin.fraction_id}" 
                                               class="form-control text-center fw-bold text-${color}" 
                                               min="0" max="${bin.max_quantity}" value="${initialValue}">
                                        <div class="small text-muted mt-1">Dostępna ilość pojemników: ${bin.max_quantity}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    binsContainer.innerHTML += cardHtml;
                });

                if (window.PREVIOUS_POST_DATA && window.PREVIOUS_POST_DATA["contact_phone"]) {
                    const prevPhone = window.PREVIOUS_POST_DATA["contact_phone"];
                    let hasOption = false;
                    for (let i = 0; i < phoneSelect.options.length; i++) {
                        if (phoneSelect.options[i].value === prevPhone) {
                            hasOption = true;
                            break;
                        }
                    }
                    if (hasOption) {
                        phoneSelect.value = prevPhone;
                    }
                }
            })
            .catch(error => {
                console.error("Błąd pobierania pojemników:", error);
                binsContainer.innerHTML = '<div class="alert alert-danger w-100">Błąd połączenia z serwerem.</div>';
            });
    });
    if (mpkSelect && mpkSelect.value) {
        // We trigger the change event but pass a custom event detail to preserve UI state if we are coming from a failed post
        const prevLocation = locationSelect.getAttribute("data-selected");
        if (prevLocation) {
            // Need to pass parameter manually to handler. Wait, Event doesn't pass args well unless CustomEvent.
            // But we already modified the handler above. Let's trigger via dispatchEvent but can't pass args directly to addEventListener change.
            // Alternative:
            mpkSelect.dispatchEvent(new Event("change"));
        } else {
            mpkSelect.dispatchEvent(new Event("change"));
        }
    } else {
        // Only disable on initial load if no MPK is selected
        if (locationSelect) locationSelect.disabled = true;
        if (phoneSelect) phoneSelect.disabled = true;
    }

    // Form Validation logic
    const pickupForm = document.getElementById("pickup-form");
    if (pickupForm) {
        pickupForm.addEventListener("submit", function(e) {
            let isValid = true;

            // Clear previous errors
            document.querySelectorAll('.is-invalid').forEach(el => {
                el.classList.remove('is-invalid');
            });
            document.querySelectorAll('.input-group.border-danger').forEach(el => {
                el.classList.remove('border-danger');
            });
            binsContainer.classList.remove('bins-error');

            if (!mpkSelect.value) {
                mpkSelect.classList.add('is-invalid');
                mpkSelect.closest('.input-group').classList.add('border-danger');
                isValid = false;
            }
            if (!locationSelect.value) {
                locationSelect.classList.add('is-invalid');
                locationSelect.closest('.input-group').classList.add('border-danger');
                isValid = false;
            }
            if (!phoneSelect.value) {
                phoneSelect.classList.add('is-invalid');
                phoneSelect.closest('.input-group').classList.add('border-danger');
                isValid = false;
            }

            // Check if at least one bin has quantity > 0
            if (locationSelect.value) {
                const binInputs = binsContainer.querySelectorAll('input[type="number"]');
                let hasBins = false;
                binInputs.forEach(input => {
                    if (parseInt(input.value) > 0) {
                        hasBins = true;
                    }
                });

                if (!hasBins && binInputs.length > 0) {
                    binsContainer.classList.add('bins-error');
                    isValid = false;
                }
            }

            if (!isValid) {
                e.preventDefault(); // Prevent form submission
            }
        });
    }
});