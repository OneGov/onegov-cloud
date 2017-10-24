var FormcodeWatcher = function() {
    var self = this;
    var subscriptions = {};

    self.subscribers = function() {
        return Object.getOwnPropertyNames(subscriptions).map(function(key) {
            return subscriptions[key];
        });
    };

    self.update = function(formcode) {
        var subscribers = self.subscribers();

        if (subscribers.length === 0) {
            return;
        }

        var success = function(fields) {
            subscribers.forEach(function(subscriber) {
                subscriber(fields);
            });
        };

        formcodeUtils.request('post', '/formcode-fields', success, formcode);
    };

    self.subscribe = function(subscriber) {
        subscriptions[subscriber] = subscriber;
    };

    self.unsubscribe = function(subscriber) {
        if (subscriptions[subscriber] !== undefined) {
            delete subscriptions[subscriber];
        }
    };

    return self;
};

var FormcodeWatcherRegistry = function() {
    var self = this;
    var watchers = {};

    self.new = function(name) {
        watchers[name] = FormcodeWatcher();
        return watchers[name];
    };

    self.get = function(name) {
        return watchers[name];
    };

    return self;
};

window.formcodeWatcherRegistry = FormcodeWatcherRegistry();
