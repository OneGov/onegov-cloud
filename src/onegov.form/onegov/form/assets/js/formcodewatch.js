var FormcodeWatcher = function() {
    var self = this;

    self.subscribers = [];

    self.update = function(formcode) {

        if (self.subscribers.length === 0) {
            return;
        }

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/formcode-fields');
        xhr.onload = function() {
            if (xhr.status === 200) {
                self.fields = JSON.parse(xhr.responseText);

                self.subscribers.forEach(function(subscriber) {
                    subscriber(self.fields);
                });
            } else {
                console.log("XHR request failed with status " + xhr.status); // eslint-disable-line no-console
            }
        };
        xhr.send(formcode);
    };

    self.subscribe = function(subscriber) {
        self.subscribers.push(subscriber);
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
