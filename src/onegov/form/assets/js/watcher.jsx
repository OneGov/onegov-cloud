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

var WatchedFields = React.createClass({
    getInitialState: function() {
        return {fields: []};
    },
    includeField: function(field) {
        if (this.props.include && this.props.include.join("")) {
            var inc = new RegExp('(' + this.props.include.join('|') + ')');
            if (!inc.test(field.type)) {
                return false;
            }
        }

        if (this.props.exclude && this.props.exclude.join("")) {
            var exc = new RegExp('(' + this.props.exclude.join('|') + ')');
            if (exc.test(field.type)) {
                return false;
            }
        }

        return true;
    },
    componentDidMount: function() {
        this.unsubscribe = this.props.watcher.subscribe(this.update);
    },
    componentWillUnmount: function() {
        this.unsubscribe();
    },
    update: function(fields) {
        if (fields.error === true) {
            return;
        }

        var filtered = [];
        var self = this;

        if (fields.forEach !== undefined) {
            fields.forEach(function(field) {
                if (self.includeField(field)) {
                    filtered.push(field);
                }
            });
        }

        this.props.handler(filtered);
    },
    render: function() {
        return (this.props.children);
    }
});
