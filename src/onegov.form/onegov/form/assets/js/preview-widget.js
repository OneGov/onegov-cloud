var PreviewWidgetHandler = function(el) {
    var fields = el.getAttribute('data-fields').split(',');
    var events = el.getAttribute('data-events').split(',');
    var url = el.getAttribute('data-url');
    var display = el.getAttribute('data-display');

    var form = (function() {
        for (var node = el; node.parentNode !== null; node = node.parentNode) {
            if (node.nodeName === 'FORM') {
                return node;
            }
        }
        return null;
    })();

    var debounce = function(callback, time) {
        var timeout;

        return function() {
            var self = this, args = arguments;

            if (timeout) {
                clearTimeout(timeout);
            }

            timeout = setTimeout(function() {
                timeout = null;
                callback.apply(self, args);
            }, time);
        };
    };

    var apply = function(html) {
        if (display === 'iframe') {
            el.innerHTML = '';

            var container = document.createElement('iframe');
            container.src = "about:blank";
            container.addEventListener('load', function() {
                container.style.height = 0;
                container.style.height = container.contentWindow.document.body.scrollHeight + 'px';
            });

            el.appendChild(container);
            container.contentWindow.document.open();
            container.contentWindow.document.write(html);
            container.contentWindow.document.close();
        } else {
            el.innerHTML = event.target.responseText;
        }
    };

    var submit = function() {
        var xhr = new XMLHttpRequest();

        xhr.addEventListener("load", function(event) {
            apply(event.target.responseText);
        });

        xhr.open("POST", url);
        xhr.send(new FormData(form));
    };

    var implementations = {
        'change': function(field) {
            field.addEventListener('change', submit, false);
        },
        'click': function(field) {
            field.addEventListener('click', submit, false);
        },
        'type': function(field) {
            field.addEventListener('keypress', debounce(function() {
                submit();
            }, 250));
        },
        'enter': function(field) {
            field.addEventListener('keypress', function(e) {
                if (e.keyCode === 13) {
                    submit();
                }
            });
        }
    };

    this.init = function() {
        fields.forEach(function(name) {
            var selector = '[name="' + name + '"]';
            var inputs = [].slice.call(form.querySelectorAll(selector)); // IE 11 NodeList to Array

            inputs.forEach(function(field) {
                events.forEach(function(event) {
                    implementations[event](field);
                });
            });
        });

        // initial load
        submit();
    };

    return this;
};

var PreviewWidgetRegistry = function(root) {
    var registry = [];

    var register = function(element) {
        registry.push(new PreviewWidgetHandler(element));
        registry[registry.length - 1].init();
    };

    this.init = function() {
        var widgets = [].slice.call(root.querySelectorAll('form .form-preview-widget'));
        widgets.forEach(register);
    };

    return this;
};

(function(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
})((new PreviewWidgetRegistry(document)).init);
