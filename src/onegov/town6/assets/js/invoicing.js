document.addEventListener('DOMContentLoaded', function() {
    setupXHREditPaymentStatus();
    setupPdfGeneration();
});

function setupXHREditPaymentStatus() {

    const markInvoicedButton = document.querySelector('.batch-action-button');
    if (markInvoicedButton) {
        markInvoicedButton.addEventListener('click', function() {
            const selectedPayments = [];
            document.querySelectorAll('input[name="selected_payments"]:checked').forEach(function(checkbox) {
                selectedPayments.push(checkbox.value);
            });

            if (selectedPayments.length === 0) {
                alert(document.documentElement.lang === 'de-CH' ? 'Bitte wählen Sie mindestens eine Zahlung aus.' : 'Please select at least one payment.');
                return;
            }

            const actionUrl = markInvoicedButton.dataset.actionUrl;
            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ payment_ids: selectedPayments })
            })
            .then(async response => {
                const text = await response.text();
                try {
                    JSON.parse(text);
                    // Many browsers cache and restore the state of form fields, that includes checkboxes
                    // This doesn't make sense heren so we uncheck them.
                    document.querySelectorAll('input[name="selected_payments"]:checked').forEach(function(checkbox) {
                        checkbox.checked = false;
                    });
                    window.location.reload();
                } catch (e) {
                    console.error('Response was not JSON:', text);
                    alert(document.documentElement.lang === 'de-CH' ? 'Ein Fehler ist aufgetreten.' : 'An error occurred.');
                }
            })
            .catch(error => {
                alert(document.documentElement.lang === 'de-CH' ? 'Ein Fehler ist aufgetreten.' : 'An error occurred.');
                console.error('Error:', error);
            });
        });
    }
}

function setupPdfGeneration() {
    const pdfButton = document.querySelector('.pdf-generation-button');
    if (pdfButton) {
        pdfButton.addEventListener('click', function(e) {
            e.preventDefault();

            // Create a form to submit with CSRF token
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = pdfButton.dataset.actionUrl;

            // Add CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            form.innerHTML = `<input type="hidden" name="csrf-token" value="${csrfToken}">`;
            document.body.appendChild(form).submit();
        });
    }
}
