var FormcodeWatcher = function(name) {
    var self = this;
    var subscriptions = {};

    self.name = name;

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
        var subscriberName = formcodeUtils.randomId('subscriber-');
        subscriptions[subscriberName] = subscriber;

        return function() {
            delete subscriptions[subscriberName];
        };
    };

    return self;
};

var FormcodeWatcherRegistry = function() {
    var self = this;
    var watchers = {};

    self.new = function(name) {
        name = name || formcodeUtils.randomId('watcher-');
        watchers[name] = FormcodeWatcher(name);
        return watchers[name];
    };

    self.get = function(name) {
        return watchers[name];
    };

    return self;
};

window.formcodeWatcherRegistry = FormcodeWatcherRegistry();
