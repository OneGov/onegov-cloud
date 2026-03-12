document.addEventListener("DOMContentLoaded", function() {
    var loadScript = function(url, callback) {
        var scriptTag = document.createElement('script');
        scriptTag.onload = callback;
        scriptTag.onreadystatechange = callback;
        scriptTag.src = url;

        document.body.appendChild(scriptTag);
    };

    var setupCheckoutButton = function(button) {
        var transaction_id = button.getAttribute('data-transaction-id');
        button.addEventListener('click', function(e) {
            e.preventDefault();
            Datatrans.startPayment({transactionId: transaction_id});
            return false;
        });
    };

    var buttons = document.querySelectorAll('.checkout-button.datatrans');

    if (buttons.length !== 0) {
        var script_url;
        if (buttons[0].hasAttribute('data-sandbox')) {
            script_url = 'https://pay.sandbox.datatrans.com/upp/payment/js/datatrans-2.0.0.js';
        } else {
            script_url = 'https://pay.datatrans.com/upp/payment/js/datatrans-2.0.0.js';
        }
        loadScript(script_url, function() {
            for (var i = 0; i < buttons.length; i++) {
                setupCheckoutButton(buttons[i]);
            }
        });
    }
});
