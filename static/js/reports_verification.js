document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('verificationForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        const decision = document.getElementById('decisionStatus').value;
        const rows = document.querySelectorAll('.fraction-row');
        
        let isValid = true;
        let anyChanges = false;
        let htmlErrorList = "";

        rows.forEach(row => {
            const supplierQty = parseInt(row.dataset.reported) || 0; 
            const confirmedInput = row.querySelector('.confirmed-qty-input');
            const confirmedQty = parseInt(confirmedInput.value) || 0;
            const noteInput = row.querySelector('.note-input');
            const noteValue = noteInput.value.trim();
            const fractionName = row.dataset.name;

            // Sprawdzamy czy nastąpiła zmiana ilości
            if (confirmedQty !== supplierQty) {
                anyChanges = true;
                
                // Walidacja 1: Brak uwagi przy rozbieżności
                if (noteValue === "") {
                    htmlErrorList += `<li><b>${fractionName}</b>: wymagana uwaga (zmiana z ${supplierQty} na ${confirmedQty})</li>`;
                    noteInput.classList.add('is-invalid');
                    isValid = false;
                }
            }
        });

        // NOWA WALIDACJA: Zmiana liczb przy statusie "Potwierdzam"
        if (anyChanges && decision === 'POTWIERDZONE') {
            e.preventDefault();
            Swal.fire({
                title: 'Niezgodność decyzji',
                html: `Wprowadzono ilości inne niż wskazane przez dostawcę. <br><br>Jeśli faktycznie odebrano inne ilości, <b>zmień decyzję na "Występują rozbieżności (Nie potwierdzam)"</b>.`,
                icon: 'warning',
                confirmButtonColor: '#0d6efd',
                confirmButtonText: 'Popraw decyzję'
            });
            return;
        }

        // Walidacja 2: Brak uwag (jeśli status był poprawny)
        if (!isValid) {
            e.preventDefault();
            Swal.fire({
                title: '<span style="color: #d33">Wymagane uzasadnienie</span>',
                icon: 'error',
                html: `<div style="text-align: left;">Proszę uzupełnić powód zmiany dla:<ul>${htmlErrorList}</ul></div>`,
                confirmButtonText: 'Popraw dane',
                confirmButtonColor: '#d33'
            });
            return;
        }

        // Walidacja 3: Status "Konflikt" bez zmian w tabeli
        if (decision === 'KONFLIKT' && !anyChanges) {
            e.preventDefault();
            Swal.fire({
                title: 'Brak rozbieżności',
                text: 'Wybrałeś status o braku potwierdzenia, ale Twoje liczby są identyczne z raportem dostawcy. Skoryguj wartości lub zmień decyzję na "Potwierdzam".',
                icon: 'info',
                confirmButtonColor: '#ffc107'
            });
        }
    });

    // Resetowanie czerwonych ramek
    document.querySelectorAll('.note-input').forEach(input => {
        input.addEventListener('input', function() {
            if (this.value.trim() !== "") this.classList.remove('is-invalid');
        });
    });
});