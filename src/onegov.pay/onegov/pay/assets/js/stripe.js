var loadScript = function(url, callback, location) {
    var scriptTag = document.createElement('script');
    scriptTag.onload = callback;
    scriptTag.onreadystatechange = callback;
    scriptTag.src = url;

    (location || document.body).appendChild(scriptTag);
};

var getStripeAttributes = function(button) {
    var attributes = [];

    for (var i = 0; i < button.attributes.length; i++) {
        var attribute = button.attributes[i];

        if (attribute.name.startsWith('data-stripe')) {
            attributes.push(attribute);
        }
    }

    return attributes;
};

var setupCheckoutButton = function(button) {
    var config = {
        token: function(token) {
            button.setAttribute('value', token.id);
        }
    };

    var attributes = getStripeAttributes(button);
    for (var i = 0; i < attributes.length; i++) {
        var attribute = attributes[i];
        config[attribute.name.replace('data-stripe-', '')] = attribute.value;
    }

    var handler = StripeCheckout.configure(config);
    button.addEventListener('click', function(e) {
        handler.open();
        e.preventDefault();
    });

    // close checkout on page navigation
    window.addEventListener('popstate', function() {
        handler.close();
    });
};

var setupCheckout = function(buttons) {
    loadScript('https://checkout.stripe.com/checkout.js', function() {
        for (var i = 0; i < buttons.length; i++) {
            setupCheckoutButton(buttons[i]);
        }
    });
};

document.addEventListener("DOMContentLoaded", function() {
    var buttons = document.querySelectorAll('.stripe-connect');

    if (buttons.length !== 0) {
        setupCheckout(buttons);
    }
});
