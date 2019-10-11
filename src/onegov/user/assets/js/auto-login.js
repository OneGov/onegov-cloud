// automatically logs in the user if loaded -> it is up to the injecting code
// to ensure that logged in users do not load this script
var attemptAutoLogin = function(url, success) {
    var request = new XMLHttpRequest();

    request.onreadystatechange = function() {
        if (request.readyState === 4 && request.status === 200) {
            success();
        }
    };

    request.open('GET', url, true);
    request.send(null);
};

// returns true if the current user agent is suspected to be a bot
var isBot = function() {
    var pattern = /bot|google|baidu|bing|msn|duckduckbot|teoma|slurp|yandex/i;

    return pattern.test(navigator.userAgent);
};

var isLoggedIn = function() {
    return document.querySelector('.is-logged-in') !== null;
};

// runs the given function at most once every n milliseconds, even across browser
// reloads, by storing the last run time in the local storage
var rateLimit = function(name, ms, fn) {
    var key = "rate-limit-" + name;
    var old = localStorage.getItem(key);

    if (old === null || (new Date() - new Date(old)) > ms) {
        localStorage.setItem(key, new Date());
        fn();
    }
};

var supportsLocalStorage = function() {
    try {
        localStorage.setItem('foo', 'bar');
        localStorage.removeItem('foo');

        return true;
    } catch (e) {

        return false;
    }
};

document.addEventListener("DOMContentLoaded", function(_event) {
    if (!isBot() && supportsLocalStorage() && !isLoggedIn()) {
        rateLimit('auto-login', 60 * 1000, function() {
            attemptAutoLogin('/auth/provider/auto', function() {
                if (window.location.pathname === "/auth/login") {
                    window.location.replace("/");
                } else {
                    window.location.reload();
                }
            });
        });
    }
});
