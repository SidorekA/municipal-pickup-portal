document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('verificationForm');
    if (!form) return;

    const decisionSelect = document.getElementById('decisionStatus');
    const saveBtn = form.querySelector('button[type="submit"]');

    // ── Walidacja inline przy każdej zmianie ilości ──────────────────
    form.addEventListener('input', function (e) {
        const input = e.target;

        if (input.classList.contains('confirmed-qty-input')) {
            handleQtyChange(input);
            updateDecisionAndButton();
        }

        if (input.classList.contains('note-input')) {
            validateNoteField(input);
            updateDecisionAndButton();
        }
    });

    function handleQtyChange(input) {
        const row       = input.closest('.fraction-row');
        const fractionId = row.dataset.fractionId;
        const supplierQty = parseInt(row.dataset.supplierQty, 10);
        const currentQty  = parseInt(input.value, 10) || 0;
        const changed     = currentQty !== supplierQty;

        // Aktualizuj klasy wiersza
        row.classList.toggle('bg-light-warning', changed);
        row.classList.toggle('border-warning', changed);

        // Styl pola ilości
        input.classList.toggle('border-warning', changed);
        input.classList.toggle('border-success', !changed && input.value !== '');

        // Pokaż lub ukryj pole uwagi
        const noteCell = form.querySelector(`[data-note-cell="${fractionId}"]`);
        if (!noteCell) return;

        const wrap = noteCell.querySelector('.note-field-wrap');
        if (!wrap) return;

        if (changed) {
            wrap.classList.remove('note-field-wrap--hidden');
            wrap.classList.add('note-field-wrap--visible');
            // Fokus na pole uwagi żeby użytkownik wiedział co uzupełnić
            const noteInput = wrap.querySelector('.note-input');
            if (noteInput && !noteInput.value.trim()) {
                setTimeout(() => noteInput.focus(), 50);
            }
        } else {
            wrap.classList.remove('note-field-wrap--visible');
            wrap.classList.add('note-field-wrap--hidden');
            const noteInput = wrap.querySelector('.note-input');
            if (noteInput) {
                noteInput.value = '';
                noteInput.classList.remove('is-invalid');
            }
        }
    }

    function validateNoteField(noteInput) {
        const wrap    = noteInput.closest('.note-field-wrap');
        const isVisible = wrap && wrap.classList.contains('note-field-wrap--visible');
        const filled  = noteInput.value.trim().length > 0;

        if (isVisible) {
            noteInput.classList.toggle('is-invalid', !filled);
            noteInput.classList.toggle('is-valid', filled);
        }
    }

    function updateDecisionAndButton() {
        let anyChange       = false;
        let anyMissingNote  = false;

        form.querySelectorAll('.fraction-row').forEach(row => {
            const qtyInput    = row.querySelector('.confirmed-qty-input');
            const supplierQty = parseInt(row.dataset.supplierQty, 10);
            const currentQty  = parseInt(qtyInput?.value, 10) || 0;
            const changed     = currentQty !== supplierQty;

            if (changed) {
                anyChange = true;
                const fractionId = row.dataset.fractionId;
                const noteCell   = form.querySelector(`[data-note-cell="${fractionId}"]`);
                const noteInput  = noteCell?.querySelector('.note-input');
                if (!noteInput || !noteInput.value.trim()) {
                    anyMissingNote = true;
                }
            }
        });

        // Auto-wybór decyzji
        if (decisionSelect && !decisionSelect.disabled) {
            decisionSelect.value = anyChange ? 'KONFLIKT' : 'POTWIERDZONE';
        }

        // Blokuj submit jeśli brakuje uzasadnień
        if (saveBtn) {
            saveBtn.disabled = anyMissingNote;
            saveBtn.title = anyMissingNote
                ? 'Uzupełnij uzasadnienie dla wszystkich zmienionych ilości'
                : '';
        }
    }

    // ── Blokada submitu — ostatnia linia obrony ───────────────────────
    form.addEventListener('submit', function (e) {
        let hasErrors = false;

        form.querySelectorAll('.fraction-row').forEach(row => {
            const qtyInput    = row.querySelector('.confirmed-qty-input');
            const supplierQty = parseInt(row.dataset.supplierQty, 10);
            const currentQty  = parseInt(qtyInput?.value, 10) || 0;

            if (currentQty !== supplierQty) {
                const fractionId = row.dataset.fractionId;
                const noteCell   = form.querySelector(`[data-note-cell="${fractionId}"]`);
                const noteInput  = noteCell?.querySelector('.note-input');

                if (!noteInput || !noteInput.value.trim()) {
                    hasErrors = true;
                    if (noteInput) noteInput.classList.add('is-invalid');
                }
            }
        });

        if (hasErrors) {
            e.preventDefault();
            // Przewiń do pierwszego błędu
            const firstInvalid = form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
        }
    });

    // ── Inicjalizacja — sprawdź stan przy załadowaniu ─────────────────
    updateDecisionAndButton();
});