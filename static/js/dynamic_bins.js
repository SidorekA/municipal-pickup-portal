document.addEventListener("DOMContentLoaded", function() {
    const mpkSelect = document.getElementById("id_mpk_number");
    const locationSelect = document.getElementById("id_location");
    const binsContainer = document.getElementById("visual-bins-container");
    const instruction = document.getElementById("bins-instruction");
    const phoneSelect = document.getElementById("id_contact_phone");

    if (!locationSelect || !binsContainer || !mpkSelect) return;

    // === INICJALIZACJA TOM SELECT ===
    let mpkTs = new TomSelect(mpkSelect, {
        placeholder: "Wybierz nr MPK",
        hideSelected: true,
        searchField: ["text"]
    });

    let locTs = new TomSelect(locationSelect, {
        placeholder: "Wybierz lokalizację",
        hideSelected: true,
        searchField: ["text"]
    });

    let initialPhoneOptions = phoneSelect ? phoneSelect.innerHTML : '';

    const colorMap = {
        'zmieszane': 'secondary',
        'makulatura': 'primary',  
        'plastik': 'warning',     
        'szkło': 'success',       
        'bio': 'success',         
    };

    function getBinColor(name) {
        const lowerName = name.toLowerCase();
        for (const [key, color] of Object.entries(colorMap)) {
            if (lowerName.includes(key)) return color;
        }
        return 'dark';
    }

    // --- FUNKCJA TWARDEGO RESETU KONTAKTÓW ---
    function resetContactsUI() {
        // 1. Całkowicie usuwamy kafelki z DOM (jeśli istnieją)
        const tileContainer = document.getElementById('contact-tiles');
        if (tileContainer) {
            tileContainer.remove(); 
        }
        // 2. Przywracamy i blokujemy klasyczny select
        if (phoneSelect) {
            phoneSelect.style.display = ''; // Usuwamy ukrycie display: none
            phoneSelect.innerHTML = initialPhoneOptions; // Przywracamy tylko "Mój numer"
            phoneSelect.value = '';
            phoneSelect.disabled = true; // Czeka na wybór lokalizacji
        }
    }

    // --- LOGIKA ZMIANY MPK ---
    mpkSelect.addEventListener("change", function() {
        const mpkId = this.value;
        const prevLocation = locationSelect.getAttribute("data-selected");
        
        locTs.clear();
        locTs.clearOptions();
        binsContainer.innerHTML = '';
        instruction.style.display = 'block';

        // TWARDY RESET PRZY ZMIANIE MPK
        resetContactsUI();

        if (mpkId) {
            locTs.disable(); 
            fetch(`/zgloszenia/api/mpk/${mpkId}/lokalizacje/`)
                .then(response => response.json())
                .then(data => {
                    data.locations.forEach(loc => {
                        locTs.addOption({value: loc.id, text: loc.name});
                    });
            
                    locTs.enable(); 

                    if (prevLocation) {
                        locTs.setValue(prevLocation);
                        locationSelect.dispatchEvent(new Event("change"));
                    }
                })
                .catch(error => {
                    console.error("Błąd pobierania lokalizacji:", error);
                    locTs.enable();
                });
        }
    });

    // --- LOGIKA ZMIANY LOKALIZACJI ---
    locationSelect.addEventListener("change", function() {
        const locationId = this.value;
        binsContainer.innerHTML = '';

        // TWARDY RESET PRZY ZMIANIE LOKALIZACJI ZANIM POBIERZEMY DANE
        resetContactsUI();

        if (!locationId) {
            instruction.style.display = 'block';
            return;
        }

        instruction.style.display = 'none';
        binsContainer.innerHTML = '<div class="text-center w-100 mt-4"><div class="spinner-border text-success"></div><p class="text-muted mt-2">Ładowanie danych...</p></div>';
        
        fetch(`/zgloszenia/api/lokalizacja/${locationId}/pojemniki/`)
            .then(response => response.json())
            .then(data => {
                binsContainer.innerHTML = '';
                
                // Budowanie kafelków kontaktów (TYLKO JEŚLI SĄ DODATKOWE KONTAKTY)
                if (data.contacts && data.contacts.length > 0) {
                    let tileContainer = document.createElement('div');
                    tileContainer.id = 'contact-tiles';
                    tileContainer.className = 'contact-tiles-wrap d-flex flex-wrap gap-2 align-items-center align-self-center';
                    
                    if (phoneSelect) {
                        phoneSelect.style.display = 'none'; // Ukrywamy klasyczny select
                        phoneSelect.disabled = false; // Odblokowujemy go do wysyłki formularza
                        phoneSelect.parentNode.insertBefore(tileContainer, phoneSelect);
                    }

                    const myPhone = phoneSelect
                        ? [...phoneSelect.options].find(o => o.text.startsWith('Mój numer'))
                        : null;

                    const allContacts = [];
                    if (myPhone) {
                        allContacts.push({ phone: myPhone.value, name: 'Mój numer', icon: 'bi-person-fill' });
                    }
                    data.contacts.forEach(c => {
                        allContacts.push({ phone: c.phone, name: c.name, icon: 'bi-building' });
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
                            tileContainer.querySelectorAll('.contact-tile').forEach(t => t.classList.remove('contact-tile--selected'));
                            this.classList.add('contact-tile--selected');
                            
                            if (phoneSelect) {
                                phoneSelect.value = contact.phone;
                                if (phoneSelect.value !== contact.phone) {
                                    const opt = new Option(contact.name, contact.phone, true, true);
                                    phoneSelect.add(opt);
                                    phoneSelect.value = contact.phone;
                                }
                            }
                        });
                        tileContainer.appendChild(tile);
                    });

                    if (allContacts.length > 0 && phoneSelect) {
                        phoneSelect.value = allContacts[0].phone;
                        if (phoneSelect.value !== allContacts[0].phone) {
                            const opt = new Option(allContacts[0].name, allContacts[0].phone, true, true);
                            phoneSelect.add(opt);
                            phoneSelect.value = allContacts[0].phone;
                        }
                    }
                } else {
                    // BRAK DODATKOWYCH KONTAKTÓW (NP. MPK 6014)
                    if (phoneSelect) {
                        phoneSelect.disabled = false;
                        for (let i = 0; i < phoneSelect.options.length; i++) {
                            if (phoneSelect.options[i].text.includes('Mój numer')) {
                                phoneSelect.selectedIndex = i;
                                break;
                            }
                        }
                    }
                }

                // Budowanie kafelków pojemników
                if (data.bins.length === 0) {
                    binsContainer.innerHTML = '<div class="alert alert-warning w-100">Brak przypisanych pojemników!</div>';
                    return;
                }

                data.bins.forEach(bin => {
                    const color = getBinColor(bin.name);
                    const icon = (function(name) {
                        const n = name.toLowerCase();
                        if (n.includes('bio')) return 'bi-tree-fill';
                        if (n.includes('szkło') || n.includes('szklo')) return 'bi-cup-straw';
                        if (n.includes('papier') || n.includes('makul')) return 'bi-box-seam';
                        if (n.includes('plastik') || n.includes('metal')) return 'bi-recycle';
                        return 'bi-trash3-fill';
                    })(bin.name);

                    const cardHtml = `
                        <div class="col-6 col-md-4 col-lg-3">
                            <div class="bin-card card h-100 border border-${color} shadow-sm" data-fraction-id="${bin.fraction_id}" data-max="${bin.max_quantity}">
                                <div class="card-body d-flex flex-column align-items-center p-3">
                                    <i class="bi ${icon} bin-icon text-${color} mb-2" aria-hidden="true"></i>
                                    <h6 class="card-title fw-bold mb-0 text-center" style="font-size:0.85rem">${bin.name}</h6>
                                    <p class="text-muted mb-3" style="font-size:0.75rem">${bin.capacity} L</p>
                                    <div class="mt-auto w-100">
                                        <div class="d-flex align-items-center justify-content-center gap-2 mb-1">
                                            <button type="button" class="btn-stepper btn-stepper-minus" data-fraction-id="${bin.fraction_id}" aria-label="Zmniejsz ilość ${bin.name} ${bin.capacity}L"><i class="bi bi-dash" aria-hidden="true"></i></button>
                                            <span class="stepper-value fw-bold text-${color}" id="stepper-val-${bin.fraction_id}" aria-live="polite">0</span>
                                            <input type="hidden" name="bin_${bin.fraction_id}" id="bin-input-${bin.fraction_id}" value="0">
                                            <button type="button" class="btn-stepper btn-stepper-plus" data-fraction-id="${bin.fraction_id}" data-max="${bin.max_quantity}" aria-label="Zwiększ ilość ${bin.name} ${bin.capacity}L"><i class="bi bi-plus" aria-hidden="true"></i></button>
                                        </div>
                                        <p class="text-muted text-center mb-0 stepper-max-info" style="font-size:0.7rem">Dostępne: <strong>${bin.max_quantity}</strong> szt.</p>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    binsContainer.innerHTML += cardHtml;
                });

                binsContainer.querySelectorAll('.btn-stepper-minus').forEach(btn => {
                    btn.disabled = true;
                });

                fetch(`/zgloszenia/api/lokalizacja/${locationId}/daty-odbioru/`)
                    .then(r => r.json())
                    .then(datesData => {
                        datesData.dates.forEach(bin => {
                            const card = binsContainer.querySelector(`[data-fraction-id="${bin.fraction_id}"]`);
                            if (!card || !bin.planned_date) return;
                            const maxInfo = card.querySelector('.stepper-max-info');
                            if (!maxInfo) return;

                            const dateEl = document.createElement('p');
                            dateEl.className = 'text-success text-center mb-0 mt-1';
                            dateEl.style.cssText = 'font-size:0.7rem;font-weight:600';
                            dateEl.innerHTML = `<i class="bi bi-calendar-check me-1" aria-hidden="true"></i>${bin.planned_date}`;
                            maxInfo.insertAdjacentElement('afterend', dateEl);
                        });
                    }).catch(() => {});

                if (window.PREVIOUS_POST_DATA) {
                    if (window.PREVIOUS_POST_DATA["contact_phone"] && phoneSelect) {
                        const prevPhone = window.PREVIOUS_POST_DATA["contact_phone"];
                        
                        const tileContainer = document.getElementById('contact-tiles');
                        if (tileContainer) {
                            tileContainer.querySelectorAll('.contact-tile').forEach(t => {
                                t.classList.remove('contact-tile--selected');
                                if (t.dataset.phone === prevPhone) {
                                    t.classList.add('contact-tile--selected');
                                }
                            });
                        }

                        let hasOption = false;
                        for (let i = 0; i < phoneSelect.options.length; i++) {
                            if (phoneSelect.options[i].value === prevPhone) {
                                hasOption = true; break;
                            }
                        }
                        if (hasOption) phoneSelect.value = prevPhone;
                    }

                    data.bins.forEach(bin => {
                        const inputName = `bin_${bin.fraction_id}`;
                        if (window.PREVIOUS_POST_DATA[inputName]) {
                            const prevQty = parseInt(window.PREVIOUS_POST_DATA[inputName], 10);
                            if (!isNaN(prevQty) && prevQty > 0) {
                                const valEl = document.getElementById('stepper-val-' + bin.fraction_id);
                                const inputEl = document.getElementById('bin-input-' + bin.fraction_id);
                                const card = document.querySelector(`[data-fraction-id="${bin.fraction_id}"]`);
                                
                                if (valEl && inputEl && card) {
                                    const max = parseInt(card.dataset.max, 10);
                                    const finalQty = Math.min(prevQty, max);

                                    valEl.textContent = finalQty;
                                    inputEl.value = finalQty;
                                    card.classList.add('bin-card--active');
                                    
                                    const minusBtn = card.querySelector('.btn-stepper-minus');
                                    const plusBtn  = card.querySelector('.btn-stepper-plus');
                                    if(minusBtn) minusBtn.disabled = false;
                                    if(plusBtn) plusBtn.disabled = (finalQty === max);
                                }
                            }
                        }
                    });
                    updateSubmitCounter();
                }

            })
            .catch(error => {
                console.error("Błąd pobierania pojemników:", error);
                binsContainer.innerHTML = '<div class="alert alert-danger w-100">Błąd połączenia z serwerem.</div>';
            });
    });

    // --- OBSŁUGA KLIKNIĘĆ W POJEMNIKI (ZDELEGOWANA NA ZEWNĄTRZ) ---
    if (binsContainer) {
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

            valEl.textContent = current;
            input.value = current;

            if (current > 0) {
                card.classList.add('bin-card--active');
            } else {
                card.classList.remove('bin-card--active');
            }

            const minusBtn = card.querySelector('.btn-stepper-minus');
            const plusBtn  = card.querySelector('.btn-stepper-plus');
            if(minusBtn) minusBtn.disabled = (current === 0);
            if(plusBtn) plusBtn.disabled  = (current === max);

            updateSubmitCounter();
        });
    }

    if (mpkSelect && mpkSelect.value) {
        const prevLocation = locationSelect.getAttribute("data-selected");
        if (prevLocation) {
            mpkSelect.dispatchEvent(new Event("change"));
        } else {
            mpkSelect.dispatchEvent(new Event("change"));
        }
    } else {
        if (locationSelect) locTs.disable();
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
            submitBtn.innerHTML = `Wyślij zgłoszenie <span class="badge bg-light text-success ms-1">${total} ${label}</span>`;
            submitBtn.disabled = false;
        } else {
            submitBtn.innerHTML = 'Wyślij zgłoszenie';
            submitBtn.disabled = false;
        }
    }

    const pickupForm = document.getElementById("pickup-form");
    if (pickupForm) {
        pickupForm.addEventListener("submit", function(e) {
            let isValid = true;

            document.querySelectorAll('.is-invalid, .border-danger').forEach(el => {
                el.classList.remove('is-invalid', 'border-danger');
            });
            binsContainer.classList.remove('bins-error');

            if (!mpkSelect.value) {
                mpkTs.wrapper.classList.add('border', 'border-danger');
                isValid = false;
            }
            if (!locationSelect.value) {
                locTs.wrapper.classList.add('border', 'border-danger');
                isValid = false;
            }
            if (!phoneSelect.value) {
                const phoneTiles = document.getElementById('contact-tiles');
                if(phoneTiles) {
                    phoneTiles.classList.add('border', 'border-danger', 'rounded', 'p-1');
                } else {
                    phoneSelect.classList.add('is-invalid');
                    phoneSelect.closest('.input-group').classList.add('border-danger');
                }
                isValid = false;
            }

            if (locationSelect.value) {
                const binInputs = binsContainer.querySelectorAll('input[type="number"], input[type="hidden"]');
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
                e.preventDefault(); 
            }
        });
    }
});