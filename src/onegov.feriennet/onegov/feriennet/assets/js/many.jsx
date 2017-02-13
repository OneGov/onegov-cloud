/*
    Provides forms with the ability to show lists of fields so the user can
    add zero, one or many things at once without leaving the form.
*/

var ManyFields = React.createClass({
    render: function() {
        return (
            <div className="many-fields">
                {
                    this.props.type === "datetime-ranges" &&
                        <ManyDateTimes
                            data={this.props.data}
                            onChange={this.props.onChange}
                        />
                }
            </div>
        );
    }
});

var ManyDateTimes = React.createClass({
    getInitialState: function() {
        var state = {
            values: _.clone(this.props.data.values)
        };

        if (state.values.length === 0) {
            state.values = [
                {'start': '', 'end': ''}
            ];
        }

        return state;
    },
    handleAdd: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index + 1, 0, {
            start: '',
            end: ''
        });
        this.setState(state);

        e.preventDefault();
    },
    handleRemove: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index, 1);
        this.setState(state);

        e.preventDefault();
    },
    handleInputChange: function(index, name, e) {
        var state = JSON.parse(JSON.stringify(this.state));

        state.values[index][name] = moment(
            e.target.value, $(e.target).data('dateformat')
        ).toDate().dateFormat('Y-m-d H:i:00').replace(' ', 'T');

        this.setState(state);

        e.preventDefault();
    },
    componentWillUpdate: function(props, state) {
        props.onChange(state);
    },
    render: function() {
        var data = this.props.data;
        var values = this.state.values;
        var self = this;
        return (
            <div> {
                _.map(values, function(value, index) {
                    var onStartChange = self.handleInputChange.bind(self, index, 'start');
                    var onEndChange = self.handleInputChange.bind(self, index, 'end');
                    var onRemove = self.handleRemove.bind(self, index);
                    var onAdd = self.handleAdd.bind(self, index);

                    return (
                        <div key={index}>
                            <div className={"row " + (value.error && 'error' || '')}>
                                <div className="small-5 columns">
                                    <DateTimeField required
                                        label={data.labels.start}
                                        defaultValue={value.start}
                                        onChange={onStartChange}
                                    />
                                </div>
                                <div className="small-5 columns">
                                    <DateTimeField required
                                        label={data.labels.end}
                                        defaultValue={value.end}
                                        onChange={onEndChange}
                                    />
                                </div>
                                <div className="small-2 columns">
                                    {
                                        index === (values.length - 1) &&
                                            <a href="#" className="button round field-button" onClick={onAdd}>
                                                <i className="fa fa-plus" aria-hidden="true"></i>
                                                <span className="show-for-sr">{data.labels.add}</span>
                                            </a>
                                    }
                                    {
                                        index > 0 && index === (values.length - 1) &&
                                            <a href="#" className="button round secondary field-button" onClick={onRemove}>
                                                <i className="fa fa-minus" aria-hidden="true"></i>
                                                <span className="show-for-sr">{data.labels.remove}</span>
                                            </a>
                                    }
                                </div>
                            </div>
                            {
                                value.error &&
                                    <div className="row date-error">
                                        <div className="small-10 columns end">
                                            <small className="error">{value.error}</small>
                                        </div>
                                    </div>
                            }
                        </div>
                    );
                })
            } </div>
        );
    }
});

var DateTimeField = React.createClass({
    componentWillMount: function() {
        this.id = _.uniqueId('datetime-');
    },
    componentDidMount: function() {
        this.renderDateTimeButton();
    },
    componentDidUpdate: function() {
        this.renderDateTimeButton();
    },
    renderDateTimeButton: function() {
        var onChange = this.props.onChange;
        if (!Modernizr.inputtypes.datetime) {
            setup_datetimepicker('datetime', '#' + this.id, function(e) {
                onChange(e);
            });
        }
    },
    render: function() {
        return (
            <label>
                <span className="label-text">{this.props.label}</span>

                {
                    this.props.required &&
                        <span className="label-required">*</span>
                }

                <input
                    id={this.id}
                    type="datetime"
                    className="small"
                    defaultValue={this.props.defaultValue}
                    onChange={this.props.onChange}
                />
            </label>
        );
    }
});

function extractType(target) {
    return _.first(_.filter(
        target.attr('class').split(' '),
        function(c) { return c.startsWith('many-'); }
    )).replace('many-', '');
}

jQuery.fn.many = function() {
    return this.each(function() {

        var target = $(this);
        var type = extractType(target);
        var data = JSON.parse(target.val());

        var label = target.closest('label');
        var errors = label.siblings('.error');

        // straight-up hiding the element prevents it from getting update
        // with the target.val call below
        label.attr('aria-hidden', true);
        label.css({
            'position': 'absolute'
        });
        label.hide();
        errors.hide();

        var el = $('<div class="many-wrapper" />');
        el.appendTo(label.parent());

        var onChange = function(newValues) {
            data.values = newValues.values;
            var json = JSON.stringify(data);
            label.show();
            target.val(json);
            label.hide();
        };

        ReactDOM.render(
            <ManyFields type={type} data={data} onChange={onChange} />,
            el.get(0)
        );
    });
};

$(document).ready(function() {
    $('.many').many();
});
