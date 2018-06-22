var FormcodeSelect = React.createClass({
    getInitialState: function() {
        var values = this.getTarget().value.split('\n').filter(function(line) {
            return line.trim() !== '';
        });

        var selected = {};
        values.forEach(function(value) {
            selected[value] = true;
        });

        return {
            fields: [],
            selected: selected
        };
    },
    getSelectionAsText: function(selected) {
        var fields = Object.getOwnPropertyNames(selected || this.state.selected);

        var order = this.state.fields.map(function(field) {
            return field.human_id;
        });

        fields.sort(function(a, b) {
            return order.indexOf(a) - order.indexOf(b);
        });

        return fields.join('\n');
    },
    getTarget: function() {
        var target = this.props.target;
        return target instanceof Element && target || document.querySelector(target);
    },
    cloneState: function() {
        return JSON.parse(JSON.stringify(this.state));
    },
    onUpdateFields: function(fields) {
        var state = this.cloneState();
        state.fields = fields;
        this.setState(state);
        this.getTarget().value = this.getSelectionAsText(state.seleted);
    },
    onSelect: function(human_id, selected) {
        var state = this.cloneState();
        if (selected) {
            state.selected[human_id] = true;
        } else {
            delete state.selected[human_id];
        }
        this.setState(state);
        this.getTarget().value = this.getSelectionAsText(state.selected);
    },
    isSelected: function(field) {
        return field.human_id in this.state.selected;
    },
    render: function() {
        var self = this;
        return (
            <WatchedFields
                include={this.props.include}
                exclude={this.props.exclude}
                watcher={this.props.watcher}
                handler={this.onUpdateFields}
            >
                <div className="formcode-select">
                    {
                        self.state.fields && self.state.fields.map(function(field) {
                            return (
                                <FormcodeSelectField
                                    key={field.id}
                                    id={field.human_id}
                                    selected={self.isSelected(field)}
                                    label={field.human_id}
                                    handler={self.onSelect}
                                />
                            );
                        })
                    }
                </div>
            </WatchedFields>
        );
    }
});

var FormcodeSelectField = React.createClass({
    getInitialState: function() {
        return {selected: this.props.selected};
    },
    handleChange: function() {
        var selected = !this.state.selected;
        this.setState({selected: selected});
        this.props.handler(this.props.id, selected);
    },
    render: function() {
        return (
            <label>
                <input
                    type="checkbox"
                    checked={this.state.selected}
                    onChange={this.handleChange}
                />
                {this.props.label}
            </label>
        );
    }
});

var initFormcodeSelect = function(container, watcher, target, include, exclude) {
    var el = container.appendChild(document.createElement('div'));
    ReactDOM.render(
        <FormcodeSelect
            watcher={watcher}
            target={target}
            include={include}
            exclude={exclude}
        />,
        el
    );
};
