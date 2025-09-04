document.addEventListener('DOMContentLoaded', function() {

    const batchStateActionButton = document.querySelector('.batch-action-button[data-action-url*="batch-set"]');
    if (batchStateActionButton) {
        batchStateActionButton.disabled = true;

        const selectAllCheckbox = document.querySelector('.select-all-checkbox-cell input[type="checkbox"]');
        const invoiceCheckboxes = document.querySelectorAll('input[name="selected_invoices"]');

        const updateButtonAndSelectAllState = function() {
            const checkedCount = document.querySelectorAll('input[name="selected_invoices"]:checked').length;
            batchStateActionButton.disabled = checkedCount === 0;
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = invoiceCheckboxes.length > 0 && checkedCount === invoiceCheckboxes.length;
            }
        };

        // Initialize button state
        updateButtonAndSelectAllState();

        const updateButtonState = function() {
            const checkedCount = document.querySelectorAll('input[name="selected_invoices"]:checked').length;
            batchStateActionButton.disabled = checkedCount === 0;
        };

        invoiceCheckboxes.forEach(function(checkbox) {
            checkbox.addEventListener('change', updateButtonState);
            checkbox.addEventListener('change', updateButtonAndSelectAllState);
        });

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                invoiceCheckboxes.forEach(function(checkbox) {
                    checkbox.checked = selectAllCheckbox.checked;
                });
                updateButtonState();
                updateButtonAndSelectAllState();
            });

        }

        batchStateActionButton.addEventListener('click', function() {
            const selectedInvoices = [];
            document.querySelectorAll('input[name="selected_invoices"]:checked').forEach(function(checkbox) {
                selectedInvoices.push(checkbox.value);
            });

            if (selectedInvoices.length === 0) {
                alert(document.documentElement.lang === 'de-CH' ? 'Bitte wählen Sie mindestens eine Rechnung aus.' : 'Please select at least one invoice.');
                return;
            }

            const stateSelect = document.getElementById('batch-invoice-state');
            const selectedState = stateSelect.value;
            const actionUrl = batchStateActionButton.dataset.actionUrl;
            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    invoice_ids: selectedInvoices,
                    state: selectedState
                })
            })
            .then(async response => {
                const text = await response.text();
                try {
                    JSON.parse(text);
                    // Many browsers cache and restore the state of form fields, that includes checkboxes
                    // This doesn't make sense here so we uncheck them.
                    document.querySelectorAll('input[name="selected_invoices"]:checked').forEach(function(checkbox) {
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
});