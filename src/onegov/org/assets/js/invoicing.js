document.addEventListener('DOMContentLoaded', function() {
    setupXHREditPaymentStatus();
});

function setupXHREditPaymentStatus() {

    // The batch-mark-invoiced functionality has been retired
    // Only using batch-set-payment-state now

    const batchStateActionButton = document.querySelector('.batch-action-button[data-action-url*="batch-set-payment-state"]');
    if (batchStateActionButton) {
        batchStateActionButton.disabled = true;

        const selectAllCheckbox = document.querySelector('.select-all-checkbox-cell input[type="checkbox"]');
        const paymentCheckboxes = document.querySelectorAll('input[name="selected_payments"]');

        const updateButtonAndSelectAllState = function() {
            const checkedCount = document.querySelectorAll('input[name="selected_payments"]:checked').length;
            batchStateActionButton.disabled = checkedCount === 0;
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = paymentCheckboxes.length > 0 && checkedCount === paymentCheckboxes.length;
            }
        };

        // Initialize button state
        updateButtonAndSelectAllState();

        const updateButtonState = function() {
            const checkedCount = document.querySelectorAll('input[name="selected_payments"]:checked').length;
            batchStateActionButton.disabled = checkedCount === 0;
        };

        paymentCheckboxes.forEach(function(checkbox) {
            checkbox.addEventListener('change', updateButtonState);
            checkbox.addEventListener('change', updateButtonAndSelectAllState);
        });

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                paymentCheckboxes.forEach(function(checkbox) {
                    checkbox.checked = selectAllCheckbox.checked;
                });
                updateButtonState();
                updateButtonAndSelectAllState();
            });

        }

        batchStateActionButton.addEventListener('click', function() {
            const selectedPayments = [];
            document.querySelectorAll('input[name="selected_payments"]:checked').forEach(function(checkbox) {
                selectedPayments.push(checkbox.value);
            });

            if (selectedPayments.length === 0) {
                alert(document.documentElement.lang === 'de-CH' ? 'Bitte wählen Sie mindestens eine Zahlung aus.' : 'Please select at least one payment.');
                return;
            }

            const stateSelect = document.getElementById('batch-payment-state');
            const selectedState = stateSelect.value;
            const actionUrl = batchStateActionButton.dataset.actionUrl;
            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    payment_ids: selectedPayments,
                    state: selectedState
                })
            })
            .then(async response => {
                const text = await response.text();
                try {
                    JSON.parse(text);
                    // Many browsers cache and restore the state of form fields, that includes checkboxes
                    // This doesn't make sense here so we uncheck them.
                    document.querySelectorAll('input[name="selected_payments"]:checked').forEach(function(checkbox) {
                        checkbox.checked = false;
                    });
                    window.location.reload();
                } catch (e) {
                    console.error('Response was not JSON:', text);
                    alert(document.documentElement.lang === 'de-CH' ? 'Ein Fehler ist aufgetreten.' : 'An error occurred.');
                }
            })
            .then(() => window.location.reload())
            .catch(error => {
                alert(document.documentElement.lang === 'de-CH' ? 'Ein Fehler ist aufgetreten.' : 'An error occurred.');
                console.error('Error:', error);
            });
        });
    }
}
