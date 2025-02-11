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
                        <ManyDateTimeRanges
                            data={this.props.data}
                            onChange={this.props.onChange}
                        />
                }
                {
                    this.props.type === "dates" &&
                        <ManyDates
                            data={this.props.data}
                            onChange={this.props.onChange}
                        />
                }
                {
                    this.props.type === "links" &&
                        <ManyLinks
                            data={this.props.data}
                            onChange={this.props.onChange}
                        />
                }

                {
                    this.props.type === "opening-hours" &&
                        <ManyOpeningHours
                            data={this.props.data}
                            onChange={this.props.onChange}
                        />
                }
            </div>
        );
    }
});

var ManyDates = React.createClass({
    getInitialState: function() {
        var state = {
            values: _.clone(this.props.data.values)
        };

        if (state.values.length === 0) {
            state.values = [
                {'date': ''}
            ];
        }

        return state;
    },
    handleAdd: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index + 1, 0, {
            date: ''
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
        var date = moment(e.target.value, $(e.target).data('dateformat'), true);

        state.values[index][name] = date.toDate().dateFormat('Y-m-d');
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
                    var onDateChange = self.handleInputChange.bind(self, index, 'date');
                    var onRemove = self.handleRemove.bind(self, index);
                    var onAdd = self.handleAdd.bind(self, index);

                    return (
                        <div key={'date-' + index}>
                            <div className={"grid-x grid-padding-x " + (value.error && 'error' || '')}>
                                <div className="small-10 cell">
                                    <DateTimePickerField required
                                        type="date"
                                        label={data.labels.date}
                                        defaultValue={value.date}
                                        onChange={onDateChange}
                                        extra={data.extra}
                                        size="normal"
                                    />
                                </div>
                                <div className="small-2 cell">
                                    {
                                        index === (values.length - 1) &&
                                            <a href="#" className="button round field-button" onClick={onAdd}>
                                                <i className="fa fa-plus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.add}</span>
                                            </a>
                                    }
                                    {
                                        values.length > 1 &&
                                            <a href="#" className="button round secondary field-button" onClick={onRemove}>
                                                <i className="fa fa-minus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.remove}</span>
                                            </a>
                                    }
                                </div>
                            </div>
                            {
                                value.error &&
                                    <div className="grid-x date-error">
                                        <div className="small-10 cell end">
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

var ManyDateTimeRanges = React.createClass({
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
                            <div className={"grid-x " + (value.error && 'error' || '')}>
                                <div className="small-5 cell">
                                    <DateTimePickerField required
                                        type="datetime"
                                        label={data.labels.start}
                                        defaultValue={value.start}
                                        onChange={onStartChange}
                                        extra={data.extra}
                                        size="small"
                                    />
                                </div>
                                <div className="small-5 cell">
                                    <DateTimePickerField required
                                        type="datetime"
                                        label={data.labels.end}
                                        defaultValue={value.end}
                                        onChange={onEndChange}
                                        extra={data.extra}
                                        size="small"
                                    />
                                </div>
                                <div className="small-2 cell">
                                    {
                                        index === (values.length - 1) &&
                                            <a href="#" className="button round field-button" onClick={onAdd}>
                                                <i className="fa fa-plus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.add}</span>
                                            </a>
                                    }
                                    {
                                        index > 0 && index === (values.length - 1) &&
                                            <a href="#" className="button round secondary field-button" onClick={onRemove}>
                                                <i className="fa fa-minus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.remove}</span>
                                            </a>
                                    }
                                </div>
                            </div>
                            {
                                value.error &&
                                    <div className="grid-x date-error">
                                        <div className="small-10 cell end">
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

var DateTimePickerField = React.createClass({
    componentWillMount: function() {
        this.id = _.uniqueId(this.props.type + '-');
    },
    componentDidMount: function() {
        this.renderDateTimeButton();
    },
    componentDidUpdate: function() {
        this.renderDateTimeButton();
    },
    renderDateTimeButton: function() {
        var onChange = this.props.onChange;

        if (!Modernizr.inputtypes[this.props.type]) {
            // ensures a valid date
            if (this.props.extra && this.props.extra.defaultDate) {
                if (isNaN(new Date(this.props.extra.defaultDate))) {
                    delete this.props.extra.defaultDate;
                } else {
                    this.props.extra.defaultDate = new Date(this.props.extra.defaultDate);
                }
            }

            setup_datetimepicker(this.props.type, '#' + this.id, function(e) {
                onChange(e);
            }, this.props.extra);
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
                    type={this.props.type}
                    className={this.props.size}
                    defaultValue={this.props.defaultValue}
                    onChange={this.props.onChange}
                />
            </label>
        );
    }
});

var ManyLinks = React.createClass({
    getInitialState: function() {
        var state = {
            values: _.clone(this.props.data.values)
        };

        if (state.values.length === 0) {
            state.values = [
                {'text': '', 'link': ''}
            ];
        }

        return state;
    },
    handleAdd: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index + 1, 0, {
            text: '',
            link: ''
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

        state.values[index][name] = e.target.value;

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
                    var onTextChange = self.handleInputChange.bind(self, index, 'text');
                    var onLinkChange = self.handleInputChange.bind(self, index, 'link');
                    var onRemove = self.handleRemove.bind(self, index);
                    var onAdd = self.handleAdd.bind(self, index);

                    return (
                        <div key={index}>
                            <div className={"grid-x grid-padding-x" + (value.error && 'error' || '')}>
                                <div className="small-6 cell">
                                    <StringField
                                        type="text"
                                        label={data.labels.text}
                                        defaultValue={value.text}
                                        onChange={onTextChange}
                                        extra={data.extra}
                                        size="small"
                                        placeholder="Linktext"
                                    />
                                </div>
                                <div className="small-6 cell">
                                    <StringField required
                                        type="text"
                                        label={data.labels.link}
                                        defaultValue={value.link}
                                        onChange={onLinkChange}
                                        extra={data.extra}
                                        size="small"
                                        placeholder="https://www.example.ch"
                                    />
                                </div>
                            </div>
                            <div className="grid-x grid-padding-x align-center">
                                <div>
                                    {
                                        index > 0 && index === (values.length - 1) &&
                                            <a href="#" className="button round secondary field-button" onClick={onRemove}>
                                                <i className="fa fa-minus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.remove}</span>
                                            </a>
                                    }
                                    {
                                        index === (values.length - 1) &&
                                            <a href="#" className="button round field-button" onClick={onAdd}>
                                                <i className="fa fa-plus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.add}</span>
                                            </a>
                                    }
                                </div>
                            </div>
                            {
                                value.error &&
                                    <div className="row error link-error">
                                        <div className="small-12 columns end">
                                            <small className="error link-error">{value.error}</small>
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

var ManyOpeningHours = React.createClass({
    getInitialState: function() {
        var state = {
            values: _.clone(this.props.data.values)
        };

        if (state.values.length === 0) {
            state.values = [
                {'day': '', 'start': '', 'end': ''}
            ];
        }

        return state;
    },
    handleAdd: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index + 1, 0, {
            text: '',
            link: ''
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

        state.values[index][name] = e.target.value;

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
                    var onDayChange = self.handleInputChange.bind(self, index, 'day');
                    var onStartChange = self.handleInputChange.bind(self, index, 'start');
                    var onEndChange = self.handleInputChange.bind(self, index, 'end');
                    var onRemove = self.handleRemove.bind(self, index);
                    var onAdd = self.handleAdd.bind(self, index);

                    return (
                        <div key={index}>
                            <div className={"grid-x grid-padding-x" + (value.error && 'error' || '')}>
                                <div className="small-2 cell">
                                    <SelectField required
                                        type="text"
                                        label={data.labels.day}
                                        defaultValue={value.day}
                                        onChange={onDayChange}
                                        extra={data.extra}
                                        size="small"
                                        placeholder={data.days[0]}
                                        options={data.days}
                                    />
                                </div>
                                <div className="small-5 cell">
                                    <StringField required
                                        type="time"
                                        label={data.labels.start}
                                        defaultValue={value.start}
                                        onChange={onStartChange}
                                        extra={data.extra}
                                        size="small"
                                        placeholder="08:00"
                                    />
                                </div>
                                <div className="small-5 cell">
                                    <StringField required
                                        type="time"
                                        label={data.labels.end}
                                        defaultValue={value.end}
                                        onChange={onEndChange}
                                        extra={data.extra}
                                        size="small"
                                        placeholder="12:00"
                                    />
                                </div>
                            </div>
                            <div className="grid-x grid-padding-x align-center">
                                <div>
                                    {
                                        index > 0 && index === (values.length - 1) &&
                                            <a href="#" className="button round secondary field-button" onClick={onRemove}>
                                                <i className="fa fa-minus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.remove}</span>
                                            </a>
                                    }
                                    {
                                        index === (values.length - 1) &&
                                            <a href="#" className="button round field-button" onClick={onAdd}>
                                                <i className="fa fa-plus" aria-hidden="true" />
                                                <span className="show-for-sr">{data.labels.add}</span>
                                            </a>
                                    }
                                </div>
                            </div>
                            {
                                value.error &&
                                    <div className="row error link-error">
                                        <div className="small-12 columns end">
                                            <small className="error link-error">{value.error}</small>
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

var SelectField = React.createClass({
    componentWillMount: function() {
        this.id = _.uniqueId(this.props.type + '-');
    },
    componentDidMount: function() {
        this.renderStringInput();
    },
    componentDidUpdate: function() {
        this.renderStringInput();
    },
    renderStringInput: function() {
        var onChange = this.props.onChange;

    },
    render: function() {
        const options = this.props.options
        return (
            <label>
                <span className="label-text">{this.props.label}</span>

                {
                    this.props.required &&
                        <span className="label-required">*</span>
                }

                <select
                    id={this.id}
                    type={this.props.type}
                    className={this.props.size}
                    defaultValue={this.props.defaultValue}
                    onChange={this.props.onChange}
                >
                    <option value="">...</option>
                {Object.keys(options).map((key, index) => (
                    <option key={index} value={key}>
                        {options[key]}
                    </option>
                ))}
                </select>
            </label>
        );
    }
});

var StringField = React.createClass({
    componentWillMount: function() {
        this.id = _.uniqueId(this.props.type + '-');
    },
    componentDidMount: function() {
        this.renderStringInput();
    },
    componentDidUpdate: function() {
        this.renderStringInput();
    },
    renderStringInput: function() {
        var onChange = this.props.onChange;

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
                    type={this.props.type}
                    className={this.props.size}
                    defaultValue={this.props.defaultValue}
                    onChange={this.props.onChange}
                    placeholder={this.props.placeholder}
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
    // Don't forget to change this file in org as well.
    return this.each(function() {

        var target = $(this);
        var type = extractType(target);
        try {
            var data = JSON.parse(target.val());
        } catch (e) {
            console.log('Failed to parse JSON:', e);
            return; // Skip this iteration if JSON is invalid
        }
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

        // Create a unique wrapper for this instance
        let wrapperId = 'many-wrapper-' + Math.random().toString(36).substr(2, 9);
        let el = $('<div class="many-wrapper" id="' + wrapperId + '" />');
        el.appendTo(label.parent());

        // transfer javascript dependencies to the wrapper
        var dependency = target.attr('data-depends-on');
        if (!_.isUndefined(dependency)) {
            target.removeAttr('data-depends-on');
            el.attr('data-depends-on', dependency);
        }

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


// since we intercept the dependency setup we need to run before document.ready
$('.many').many();
