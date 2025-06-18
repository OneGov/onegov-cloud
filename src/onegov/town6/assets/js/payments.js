document.addEventListener('DOMContentLoaded', function() {
    setupXHREditPaymentStatus();
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
                alert(document.documentElement.lang === 'de' ? 'Bitte wählen Sie mindestens eine Zahlung aus.' : 'Please select at least one payment.');
                return;
            }

            const actionUrl = markInvoicedButton.dataset.actionUrl;
            const csrfToken = markInvoicedButton.dataset.csrfToken;

            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ payment_ids: selectedPayments })
            })
            .then(response => response.json())
            .then(data => {
                window.location.reload();
            })
            .catch(error => {
                alert(document.documentElement.lang === 'de' ? 'Ein Fehler ist aufgetreten.' : 'An error occurred.');
                console.error('Error:', error);
            });
        });
    }
}
