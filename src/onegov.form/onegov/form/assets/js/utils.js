var FormcodeUtils = function() {
    var self = this;

    self.updateTarget = function(target, value, extra, separator) {
        // if the target is an element, add to its value
        var element = document.querySelector(target);
        if (element) {
            if (element.value === '') {
                element.value = value;
            } else {
                element.value += (separator || '\n') + value;
            }
            return;
        }

        // otherwise assume it is a function stored on the window
        var fn = window[target];
        if (fn) {
            fn(value, extra);
            return;
        }
    };

    self.request = function(method, url, success, body) {
        var xhr = new XMLHttpRequest();
        xhr.open(method.toUpperCase(), url);
        xhr.onload = function() {
            if (xhr.status === 200) {
                success(JSON.parse(xhr.responseText));
            } else {
                console.log(method + " " + url + " failed with status " + xhr.status); // eslint-disable-line no-console
            }
        };
        xhr.send(body);
    };

    return self;
};

window.formcodeUtils = FormcodeUtils();
