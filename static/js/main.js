/**
 * FRICA Rental App – Client-Side Interactivity v2
 * Covers: Live rental calculator with GST, date validation, payment highlighting, alert auto-dismiss
 */

document.addEventListener('DOMContentLoaded', function () {
    initRentalCalculator();
    initPaymentSelection();
    initAlertAutoDismiss();
    initDateConstraints();
});

/* ─── 1. Rental Calculator (product_detail page) ─────────────────────── */
function initRentalCalculator() {
    const startInput = document.getElementById('id_rent_start_date');
    const endInput   = document.getElementById('id_rent_end_date');
    const priceEl    = document.getElementById('daily-price-val');

    if (!startInput || !endInput || !priceEl) return;

    const dailyRate = parseFloat(priceEl.dataset.price || '0');

    const displayDays     = document.getElementById('display-total-days');
    const displaySubtotal = document.getElementById('display-subtotal');
    const displayGst      = document.getElementById('display-gst');
    const displayTotal    = document.getElementById('display-total-price');
    const calcFormula     = document.getElementById('calc-formula');
    const dateFeedback    = document.getElementById('date-feedback');
    const submitBtn       = document.getElementById('rent-submit-btn');

    function fmt(num) {
        return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function calculate() {
        const startVal = startInput.value;
        const endVal   = endInput.value;
        if (!startVal || !endVal) return;

        const start = new Date(startVal + 'T00:00:00');
        const end   = new Date(endVal   + 'T00:00:00');
        const now   = new Date(); now.setHours(0,0,0,0);

        // Validate
        if (start < now) {
            showError('Start date cannot be in the past.');
            return;
        }
        if (end < start) {
            showError('Return date must be equal to or after the pickup date.');
            return;
        }
        clearError();

        const days      = Math.round((end - start) / 864e5) + 1;
        const subtotal  = days * dailyRate;
        const gst       = subtotal * 0.18;
        const total     = subtotal + gst;

        if (displayDays)     displayDays.textContent     = days + (days === 1 ? ' Day' : ' Days');
        if (calcFormula)     calcFormula.textContent      = `(${days} × ₹${dailyRate.toLocaleString('en-IN')})`;
        if (displaySubtotal) displaySubtotal.textContent  = fmt(subtotal);
        if (displayGst)      displayGst.textContent       = fmt(gst);
        if (displayTotal)    displayTotal.textContent     = fmt(total);
        if (submitBtn)       submitBtn.disabled           = false;
    }

    function showError(msg) {
        if (dateFeedback) { dateFeedback.textContent = msg; dateFeedback.classList.remove('d-none'); }
        if (submitBtn) submitBtn.disabled = true;
    }
    function clearError() {
        if (dateFeedback) dateFeedback.classList.add('d-none');
    }

    startInput.addEventListener('change', function () {
        if (startInput.value) {
            endInput.min = startInput.value;
            if (endInput.value && endInput.value < startInput.value) {
                endInput.value = startInput.value;
            }
        }
        calculate();
    });

    endInput.addEventListener('change', calculate);

    // Trigger on load
    calculate();
}

/* ─── 2. Enforce today as min for all date pickers ───────────────────── */
function initDateConstraints() {
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[name="rent_start_date"]').forEach(el => {
        if (!el.min) el.min = today;
    });
}

/* ─── 3. Payment option card highlighting (checkout page) ────────────── */
function initPaymentSelection() {
    const radios = document.querySelectorAll('input[name="payment_method"]');
    function highlightSelected() {
        document.querySelectorAll('.payment-option-card').forEach(card => {
            card.classList.remove('border-primary', 'shadow-sm');
            card.style.background = '';
        });
        const checked = document.querySelector('input[name="payment_method"]:checked');
        if (checked) {
            const card = checked.closest('.payment-option-card');
            if (card) {
                card.classList.add('border-primary', 'shadow-sm');
                card.style.background = 'var(--primary-light)';
            }
        }
    }
    radios.forEach(r => r.addEventListener('change', highlightSelected));
    highlightSelected(); // Apply on load
}

/* ─── 4. Auto-dismiss Bootstrap alerts after 6 s ────────────────────── */
function initAlertAutoDismiss() {
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            const instance = bootstrap && bootstrap.Alert && bootstrap.Alert.getOrCreateInstance(alert);
            if (instance) instance.close();
        }, 6000);
    });
}
