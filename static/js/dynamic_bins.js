document.addEventListener("DOMContentLoaded", function() {
    const mpkSelect = document.getElementById("id_mpk_number");
    const locationSelect = document.getElementById("id_location");
    const binsContainer = document.getElementById("visual-bins-container");
    const instruction = document.getElementById("bins-instruction");

    if (!locationSelect || !binsContainer || !mpkSelect) return;

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
        
        locationSelect.innerHTML = '<option value="">---------</option>';
        binsContainer.innerHTML = '';
        instruction.style.display = 'block';

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
        binsContainer.innerHTML = '<div class="text-center w-100"><div class="spinner-border text-success"></div></div>';

        fetch(`/zgloszenia/api/lokalizacja/${locationId}/pojemniki/`)
            .then(response => response.json())
            .then(data => {
                binsContainer.innerHTML = '';
                
                if (data.bins.length === 0) {
                    binsContainer.innerHTML = '<div class="alert alert-warning w-100">Brak przypisanych pojemników dla tej lokalizacji!</div>';
                    return;
                }

                data.bins.forEach(bin => {
                    const color = getBinColor(bin.name);
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
                                               min="0" max="${bin.max_quantity}" value="0">
                                        <div class="small text-muted mt-1">Zgłoszono w systemie: ${bin.max_quantity}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    binsContainer.innerHTML += cardHtml;
                });
            })
            .catch(error => {
                console.error("Błąd pobierania pojemników:", error);
                binsContainer.innerHTML = '<div class="alert alert-danger w-100">Błąd połączenia z serwerem.</div>';
            });
    });
});