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
                {
                    this.props.type === "firebasetopics" &&
                        <ManyFirebasetopics
                            data={this.props.data}
                            onChange={this.props.onChange}
                        />
                }
                {
                    this.props.type === "meeting-items" &&
                        <ManyMeetingItems
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

var ManyFirebasetopics = React.createClass({
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
    componentWillMount: function() {
        // Generate unique IDs for datalists once at component level
        this.textListId = _.uniqueId('topic-ids-');
        this.linkListId = _.uniqueId('topic-names-');
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

        // Get options from the data
        var textOptions = data.textOptions || [];
        var linkOptions = data.linkOptions || [];

        var textPlaceholder = (data.placeholders && data.placeholders.text) || "Key";
        var linkPlaceholder = (data.placeholders && data.placeholders.link) || "Label";

        return (
            <div>
                {/* Create datalists once at the component level */}
                {textOptions.length > 0 && (
                    <datalist id={this.textListId}>
                        {textOptions.map(function(option, i) {
                            return <option key={i} value={option} />;
                        })}
                    </datalist>
                )}

                {linkOptions.length > 0 && (
                    <datalist id={this.linkListId}>
                        {linkOptions.map(function(option, i) {
                            return <option key={i} value={option} />;
                        })}
                    </datalist>
                )}

                {_.map(values, function(value, index) {
                    var onTextChange = self.handleInputChange.bind(self, index, 'text');
                    var onLinkChange = self.handleInputChange.bind(self, index, 'link');
                    var onRemove = self.handleRemove.bind(self, index);
                    var onAdd = self.handleAdd.bind(self, index);

                    return (
                        <div key={index}>
                            <div className={"grid-x grid-padding-x" + (value.error && 'error' || '')}>
                                <div className="small-6 cell">
                                    <StringField required
                                        type="text"
                                        label={data.labels.text}
                                        defaultValue={value.text}
                                        onChange={onTextChange}
                                        extra={data.extra}
                                        size="small"
                                        placeholder={textPlaceholder}
                                        options={textOptions}
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
                                                 placeholder={linkPlaceholder}
                                                 options={linkOptions}
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
                                <div className="row firebase-error">
                                    <div className="small-12 columns end">
                                        <small className="error">{value.error}</small>
                                    </div>
                                </div>
                            }
                        </div>
                    );
                })}
            </div>
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
        this.setState(state, () => {
            // the select field of ManyMeetingItems uses jquery `chosen`
            // plugin which needs to be reinitialized after the react
            // component state has been updated
            jQuery('.chosen-select').chosen({});
        });

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


var ManyMeetingItems = React.createClass({
    getInitialState: function() {
        var state = {
            values: _.clone(this.props.data.values)
        };

        if (state.values.length === 0) {
            state.values = [
                {'number': '', 'title': '', 'agenda_item': ''}
            ];
        }

        return state;
    },
    handleAdd: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index + 1, 0, {
            number: '',
            title: '',
            agenda_item: ''
        });
        this.setState(state, () => {
            // the select field of ManyMeetingItems uses jquery `chosen`
            // plugin which needs to be reinitialized after the react
            // component state has been updated
            jQuery('.chosen-select').chosen({});
        });

        e.preventDefault();
    },
    handleRemove: function(index, e) {
        var state = JSON.parse(JSON.stringify(this.state));
        state.values.splice(index, 1);

        this.setState(state);

        if (state.values.length === 0) {
            // If all items are removed, reload the page to reset the form
            // as not any chosen item is left
            window.location.reload();
        }

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
                    var onNumberChange = self.handleInputChange.bind(self, index, 'number');
                    var onTitleChange = self.handleInputChange.bind(self, index, 'title');
                    var onAgendaItemChange = self.handleInputChange.bind(self, index, 'agenda_item');
                    var onRemove = self.handleRemove.bind(self, index);
                    var onAdd = self.handleAdd.bind(self, index);

                    return (
                        <div key={index}>
                            <div className={"grid-x grid-padding-x" + (value.error && 'error' || '')}>
                                <div className="small-2 cell">
                                    <StringField
                                        type="text"
                                        label={data.labels.number}
                                        defaultValue={value.number}
                                        onChange={onNumberChange}
                                        extra={data.extra}
                                        size="x-small"
                                        placeholder=""
                                    />
                                </div>
                                <div className="small-5 cell">
                                    <StringField
                                        type="text"
                                        label={data.labels.title}
                                        defaultValue={value.title}
                                        onChange={onTitleChange}
                                        extra={data.extra}
                                        size="medium"
                                        placeholder=""
                                    />
                                </div>
                                <div className="small-5 cell">
                                    <SelectField
                                        type="text"
                                        label={data.labels.agenda_item}
                                        defaultValue={value.agenda_item}
                                        onChange={onAgendaItemChange}
                                        extra={data.extra}
                                        size="medium"
                                        placeholder={data.agenda_items[0]}
                                        options={data.agenda_items}
                                    />
                                </div>
                            </div>
                            <div className="grid-x grid-padding-x align-center">
                                <div>
                                    {
                                        index >= 0 && index === (values.length - 1) &&
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

        // chosen-select: forward jquery change event to React onChange
        $(`#${this.id}`).on('change', (e) => {
            this.props.onChange(e);
        });
    },
    componentDidUpdate: function() {
        this.renderStringInput();
    },
    renderStringInput: function() {
        var onChange = this.props.onChange;
    },

    render: function() {
        const options = this.props.options
        const className = this.props.size + " chosen-select";

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
                    className={className}
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
        this.datalistId = this.id + '-list';
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
        // Check if options were provided for datalist
        const hasOptions = this.props.options && this.props.options.length > 0;

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
                    list={hasOptions ? this.datalistId : undefined}
                />

                {/* Add datalist for autocomplete if options are provided */}
                {hasOptions && (
                    <datalist id={this.datalistId}>
                        {this.props.options.map((option, index) => (
                            <option key={index} value={option} />
                        ))}
                    </datalist>
                )}
            </label>
        );
    }
});


function extractType(target) {
    // More robust type extraction
    var classes = target.attr('class').split(' ');

    // Special case for firebase topics
    if (classes.includes('many-firebasetopics')) {
        return 'firebasetopics';
    }

    if (classes.includes('many-meeting-items')) {
        return 'meeting-items';
    }

    var manyClass = classes.find(function(c) {
        return c.startsWith('many-');
    });
    return manyClass ? manyClass.replace('many-', '') : 'links'; // Default to links if no type found
}

jQuery.fn.many = function () {
    return this.each(function (index) {
        var target = $(this);
        var type = extractType(target);

        // Safely parse data with fallback
        var rawValue = target.val();
        var data;

        try {
            data = rawValue ? JSON.parse(rawValue) : null;
        } catch (e) {
            console.warn('Failed to parse JSON for many-' + type, e);
            data = null;
        }

        // Provide default data structure if needed
        if (!data) {
            if (type === 'firebasetopics') {
                // Default structure for Firebase topics
                data = {
                    labels: {
                        text: 'Key',
                        link: 'Label',
                        add: 'Hinzufügen',
                        remove: 'Entfernen'
                    },
                    placeholders: {
                        text: 'Key auswählen',
                        link: 'Label auswählen'
                    },
                    textOptions: [],
                    linkOptions: [],
                    values: []
                };
            } else if (type === 'meeting-items') {
                data = {
                    labels: {
                        title: 'Title',
                        agenda_item: 'Agenda Item',
                        add: 'Hinzufügen',
                        remove: 'Entfernen'
                    },
                    placeholders: {
                        title: 'Title',
                        agenda_item: 'Select Agenda Item'
                    },
                    textOptions: [],
                    linkOptions: [],
                    values: []
                };
            } else {
                // Default structure for other types
                data = {
                    labels: {
                        text: type === 'contactlinks' ? 'Contact Text' : 'Text',
                        link: type === 'contactlinks' ? 'Contact URL' : 'URL',
                        add: 'Add',
                        remove: 'Remove'
                    },
                    values: []
                };
            }
        }

        var label = target.closest('label');
        var wrapperId = 'many-wrapper-' + Math.random().toString(36).substr(2, 9);
        var el = $('<div class="many-wrapper" id="' + wrapperId + '" />');

        label.attr('aria-hidden', true);
        label.css({
            'position': 'absolute',
            'visibility': 'hidden'
        });

        el.appendTo(label.parent());

        var dependency = target.attr('data-depends-on');
        if (dependency) {
            target.removeAttr('data-depends-on');
            el.attr('data-depends-on', dependency);
        }

        var onChange = function (newValues) {
            data.values = newValues.values;
            var json = JSON.stringify(data);
            target.val(json);
        };

        try {
            ReactDOM.render(
                React.createElement(ManyFields, {
                    type: type,
                    data: data,
                    onChange: onChange
                }),
                document.getElementById(wrapperId)
            );
        } catch (e) {
            console.error('Failed to render ManyFields for ' + type, e);
            el.remove();
            label.css({
                'position': 'static',
                'visibility': 'visible'
            });
        }
    });
}

// since we intercept the dependency setup we need to run before document.ready
$('.many').many();
