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
                
                if (data.contacts && data.contacts.length > 0) {
                    // Znajdź lub stwórz kontener kafelków
                    let tileContainer = document.getElementById('contact-tiles');
                    if (!tileContainer) {
                        tileContainer = document.createElement('div');
                        tileContainer.id = 'contact-tiles';
                        tileContainer.className = 'contact-tiles-wrap mb-3';
                        // Wstaw przed selectem (ukrytym) lub jako jego zamiennik
                        if (phoneSelect) {
                            phoneSelect.style.display = 'none';
                            phoneSelect.parentNode.insertBefore(tileContainer, phoneSelect);
                        }
                    }
                    tileContainer.innerHTML = '';

                    // Dodaj opcję "mój numer" jeśli wypełnione w profilu
                    const myPhone = phoneSelect
                        ? [...phoneSelect.options].find(o => o.text.startsWith('Mój numer'))
                        : null;

                    const allContacts = [];

                    if (myPhone) {
                        allContacts.push({
                            phone: myPhone.value,
                            name: 'Mój numer',
                            icon: 'bi-person-fill'
                        });
                    }

                    data.contacts.forEach(c => {
                        allContacts.push({
                            phone: c.phone,
                            name: c.name,
                            icon: 'bi-building'
                        });
                    });

                    allContacts.forEach((contact, idx) => {
                        const tile = document.createElement('button');
                        tile.type = 'button';
                        tile.className = 'contact-tile' + (idx === 0 ? ' contact-tile--selected' : '');
                        tile.dataset.phone = contact.phone;
                        tile.innerHTML = `
                            <i class="bi ${contact.icon} contact-tile__icon" aria-hidden="true"></i>
                            <span class="contact-tile__name">${contact.name}</span>
                            <span class="contact-tile__phone">${contact.phone}</span>
                        `;
                        tile.addEventListener('click', function () {
                            // Odznacz wszystkie, zaznacz kliknięty
                            tileContainer.querySelectorAll('.contact-tile').forEach(t => {
                                t.classList.remove('contact-tile--selected');
                            });
                            this.classList.add('contact-tile--selected');
                            // Zaktualizuj ukryty select
                            if (phoneSelect) {
                                phoneSelect.value = contact.phone;
                                // Jeśli wartość nie istnieje w options, dodaj ją
                                if (phoneSelect.value !== contact.phone) {
                                    const opt = new Option(contact.name, contact.phone, true, true);
                                    phoneSelect.add(opt);
                                    phoneSelect.value = contact.phone;
                                }
                            }
                        });
                        tileContainer.appendChild(tile);
                    });

                    // Zaznacz pierwszy kafelek i ustaw wartość selecta
                    if (allContacts.length > 0 && phoneSelect) {
                        phoneSelect.value = allContacts[0].phone;
                        if (phoneSelect.value !== allContacts[0].phone) {
                            const opt = new Option(allContacts[0].name, allContacts[0].phone, true, true);
                            phoneSelect.add(opt);
                            phoneSelect.value = allContacts[0].phone;
                        }
                    }
                }

                if (data.bins.length === 0) {
                    binsContainer.innerHTML = '<div class="alert alert-warning w-100">Brak przypisanych pojemników dla tej lokalizacji!</div>';
                    return;
                }

                data.bins.forEach(bin => {
                    const color = getBinColor(bin.name);

                    // Wybierz ikonę Bootstrap Icons na podstawie nazwy frakcji
                    function getBinIcon(name) {
                        const n = name.toLowerCase();
                        if (n.includes('bio'))      return 'bi-tree-fill';
                        if (n.includes('szkło') || n.includes('szklo')) return 'bi-cup-straw';
                        if (n.includes('papier') || n.includes('makul')) return 'bi-box-seam';
                        if (n.includes('plastik') || n.includes('metal')) return 'bi-recycle';
                        return 'bi-trash3-fill';
                    }

                    const icon = getBinIcon(bin.name);

                    const cardHtml = `
                        <div class="col-6 col-md-4 col-lg-3">
                            <div class="bin-card card h-100 border border-${color} shadow-sm"
                                 data-fraction-id="${bin.fraction_id}"
                                 data-max="${bin.max_quantity}">
                                <div class="card-body d-flex flex-column align-items-center p-3">

                                    <i class="bi ${icon} bin-icon text-${color} mb-2"></i>
                                    <h6 class="card-title fw-bold mb-0 text-center"
                                        style="font-size:0.85rem">${bin.name}</h6>
                                    <p class="text-muted mb-3" style="font-size:0.75rem">
                                        ${bin.capacity} L
                                    </p>

                                    <!-- Stepper -->
                                    <div class="mt-auto w-100">
                                        <div class="d-flex align-items-center justify-content-center gap-2 mb-1">
                                            <button type="button"
                                                    class="btn-stepper btn-stepper-minus"
                                                    aria-label="Zmniejsz ilość ${bin.name}"
                                                    data-fraction-id="${bin.fraction_id}">
                                                <i class="bi bi-dash" aria-hidden="true"></i>
                                            </button>

                                            <span class="stepper-value fw-bold text-${color}"
                                                  id="stepper-val-${bin.fraction_id}"
                                                  aria-live="polite"
                                                  aria-label="Ilość: 0 pojemników">0</span>

                                            <!-- Ukryte pole POST — to wysyłamy do backendu -->
                                            <input type="hidden"
                                                   name="bin_${bin.fraction_id}"
                                                   id="bin-input-${bin.fraction_id}"
                                                   value="0">

                                            <button type="button"
                                                    class="btn-stepper btn-stepper-plus"
                                                    aria-label="Zwiększ ilość ${bin.name}"
                                                    data-fraction-id="${bin.fraction_id}"
                                                    data-max="${bin.max_quantity}">
                                                <i class="bi bi-plus" aria-hidden="true"></i>
                                            </button>
                                        </div>

                                        <p class="text-muted text-center mb-0 stepper-max-info"
                                           style="font-size:0.7rem">
                                            Dostępne: <strong>${bin.max_quantity}</strong> szt.
                                        </p>
                                    </div>

                                </div>
                            </div>
                        </div>
                    `;
                    binsContainer.innerHTML += cardHtml;
                });

                // Delegacja zdarzeń na kontener — obsługuje wszystkie steppery
                binsContainer.addEventListener('click', function(e) {
                    const btn = e.target.closest('.btn-stepper');
                    if (!btn) return;

                    const fractionId = btn.dataset.fractionId;
                    const valEl  = document.getElementById('stepper-val-' + fractionId);
                    const input  = document.getElementById('bin-input-' + fractionId);
                    const card   = btn.closest('.bin-card');
                    const max    = parseInt(card.dataset.max, 10);

                    let current = parseInt(valEl.textContent, 10);

                    if (btn.classList.contains('btn-stepper-plus')) {
                        if (current < max) current++;
                    } else {
                        if (current > 0) current--;
                    }

                    // Aktualizuj wyświetlaną wartość i ukryte pole
                    valEl.textContent = current;
                    valEl.setAttribute('aria-label', `Ilość: ${current} pojemników`);
                    input.value = current;

                    // Wizualne podświetlenie aktywnej karty
                    if (current > 0) {
                        card.classList.add('bin-card--active');
                    } else {
                        card.classList.remove('bin-card--active');
                    }

                    // Blokuj przycisk minus przy 0, plus przy max
                    const minusBtn = card.querySelector('.btn-stepper-minus');
                    const plusBtn  = card.querySelector('.btn-stepper-plus');
                    minusBtn.disabled = (current === 0);
                    plusBtn.disabled  = (current === max);

                    // Zaktualizuj licznik w przycisku submit
                    updateSubmitCounter();
                });

                // Inicjalizacja — zablokuj wszystkie przyciski minus na starcie
                binsContainer.querySelectorAll('.btn-stepper-minus').forEach(btn => {
                    btn.disabled = true;
                });

                // Pobierz i wyświetl planowane daty odbioru
                fetch(`/zgloszenia/api/lokalizacja/${locationId}/daty-odbioru/`)
                    .then(r => r.json())
                    .then(datesData => {
                        datesData.dates.forEach(item => {
                            const card = binsContainer.querySelector(
                                `[data-fraction-id="${item.fraction_id}"]`
                            );
                            if (!card || !item.planned_date) return;

                            const maxInfo = card.querySelector('.stepper-max-info');
                            if (!maxInfo) return;

                            // Dodaj datę odbioru pod info o dostępności
                            const dateEl = document.createElement('p');
                            dateEl.className = 'text-success text-center mb-0 mt-1';
                            dateEl.style.cssText = 'font-size:0.7rem;font-weight:600';
                            dateEl.innerHTML =
                                `<i class="bi bi-calendar-check me-1" aria-hidden="true"></i>` +
                                `${item.planned_date}`;
                            maxInfo.insertAdjacentElement('afterend', dateEl);
                        });
                    })
                    .catch(() => {
                        // Cicha obsługa błędu — data odbioru jest informacyjna
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

    function updateSubmitCounter() {
        const submitBtn = document.querySelector('#pickup-form button[type="submit"]');
        if (!submitBtn) return;

        let total = 0;
        document.querySelectorAll('[id^="stepper-val-"]').forEach(el => {
            total += parseInt(el.textContent, 10) || 0;
        });

        if (total > 0) {
            const label = total === 1 ? 'pojemnik' :
                          total < 5  ? 'pojemniki' : 'pojemników';
            submitBtn.innerHTML =
                `Wyślij zgłoszenie <span class="badge bg-light text-success ms-1">${total} ${label}</span>`;
            submitBtn.disabled = false;
        } else {
            submitBtn.innerHTML = 'Wyślij zgłoszenie';
            submitBtn.disabled = false;
        }
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