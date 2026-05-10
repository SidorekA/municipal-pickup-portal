document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('verificationForm');
    const submitBtn = document.getElementById('submitBtn');
    const decisionStatus = document.getElementById('decisionStatus');
    const rows = document.querySelectorAll('.fraction-row');

    if (!form) return;

    function evaluateForm() {
        let anyChanges = false;
        let allNotesFilled = true;

        rows.forEach(row => {
            const confirmedInput = row.querySelector('.confirmed-qty-input');
            if (!confirmedInput) return; // pomin jesli readonly lub cos

            const supplierQty = parseInt(confirmedInput.dataset.dostawca) || 0;
            const confirmedQty = parseInt(confirmedInput.value) || 0;
            const noteInput = row.querySelector('.note-input');
            const complianceText = row.querySelector('.compliance-text');

            // Jeśli ilości są równe (zgodność)
            if (confirmedQty === supplierQty) {
                if (noteInput) {
                    noteInput.classList.add('d-none');
                    noteInput.classList.remove('is-invalid');
                    noteInput.classList.remove('fade-in');
                    noteInput.value = "";
                }
                if (complianceText) complianceText.classList.remove('d-none');
                row.classList.remove('bg-light-warning');
                confirmedInput.classList.remove('border-warning');
            }
            // Jeśli się różnią (rozbieżność)
            else {
                anyChanges = true;
                
                if (complianceText) complianceText.classList.add('d-none');
                row.classList.add('bg-light-warning');
                confirmedInput.classList.add('border-warning');

                if (noteInput) {
                    if (noteInput.classList.contains('d-none')) {
                        noteInput.classList.remove('d-none');
                        noteInput.classList.add('fade-in');
                    }

                    if (noteInput.value.trim() === "") {
                        noteInput.classList.add('is-invalid');
                        allNotesFilled = false;
                    } else {
                        noteInput.classList.remove('is-invalid');
                    }
                }
            }
        });

        // Globalna ewaluacja
        if (anyChanges) {
            if (decisionStatus && !decisionStatus.disabled) {
                decisionStatus.value = 'KONFLIKT';
            }
        } else {
            if (decisionStatus && !decisionStatus.disabled) {
                decisionStatus.value = 'POTWIERDZONE';
            }
        }

        // Blokada submit
        if (submitBtn) {
            if (anyChanges && !allNotesFilled) {
                submitBtn.disabled = true;
            } else {
                submitBtn.disabled = false;
            }
        }
    }

    // Podpięcie zdarzeń
    rows.forEach(row => {
        const confirmedInput = row.querySelector('.confirmed-qty-input');
        const noteInput = row.querySelector('.note-input');

        if (confirmedInput) {
            confirmedInput.addEventListener('input', evaluateForm);
        }
        if (noteInput) {
            noteInput.addEventListener('input', evaluateForm);
        }
    });

    // Uruchomienie ewaluacji przy starcie, aby upewnić się, że stan jest poprawny
    evaluateForm();

    form.addEventListener('submit', function(e) {
        // Dodatkowe zabezpieczenie przed nieprawidłowym wysłaniem
        evaluateForm();
        if (submitBtn && submitBtn.disabled) {
            e.preventDefault();
            Swal.fire({
                title: '<span style="color: #d33">Wymagane uzasadnienie</span>',
                icon: 'error',
                html: 'Proszę uzupełnić wszystkie powody zmian w polach zaznaczonych na czerwono.',
                confirmButtonText: 'Rozumiem',
                confirmButtonColor: '#d33'
            });
        }
    });
});