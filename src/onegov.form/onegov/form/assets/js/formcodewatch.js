var FormcodeWatcher = function() {
    var self = this;
    var subscriptions = {};

    self.subscribers = function() {
        var result = [];

        for (var key in subscriptions) {
            if (subscriptions.hasOwnProperty(key)) {
                result.push(subscriptions[key]);
            }
        }

        return result;
    };

    self.fetch = function(formcode, success) {
        var xhr = new XMLHttpRequest();

        xhr.open('POST', '/formcode-fields');
        xhr.onload = function() {
            if (xhr.status === 200) {
                success(JSON.parse(xhr.responseText));
            } else {
                console.log("XHR request failed with status " + xhr.status); // eslint-disable-line no-console
            }
        };
        xhr.send(formcode);
    };

    self.update = function(formcode) {
        var subscribers = self.subscribers();

        if (subscribers.length === 0) {
            return;
        }

        self.fetch(formcode, function(fields) {
            subscribers.forEach(function(subscriber) {
                subscriber(fields);
            });
        });
    };

    self.subscribe = function(subscriber) {
        subscriptions[subscriber] = subscriber;
    };

    self.unsubscribe = function(subscriber) {
        if (subscriptions[subscriber] === undefined) {
            delete subscriptions[subscriber];
        }
    };

    return self;
};

var FormcodeWatcherRegistry = function() {
    var self = this;
    self.watchers = {};

    self.new = function(name) {
        self.watchers[name] = FormcodeWatcher();
        return self.watchers[name];
    };

    self.get = function(name) {
        return self.watchers[name];
    };

    return self;
};

window.formcodeWatcherRegistry = FormcodeWatcherRegistry();
