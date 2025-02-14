document.addEventListener("DOMContentLoaded", function() {
    var setupCheckoutButton = function(button) {
        var url = button.getAttribute('data-redirect-url');
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.replace(url);
            return false;
        });
    };

    var buttons = document.querySelectorAll('.checkout-button.saferpay');
    if (buttons.length !== 0) {
        for (var i = 0; i < buttons.length; i++) {
            setupCheckoutButton(buttons[i]);
        }
    }
});
