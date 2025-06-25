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
                    console.log(text)
                    const data = JSON.parse(text);
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
