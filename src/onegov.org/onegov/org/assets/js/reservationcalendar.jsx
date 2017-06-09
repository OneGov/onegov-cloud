/*
    The reservation calendar extends fullcalendar adding methods to allocate
    dates, select and then reserve them.
*/

var rc = $.reservationCalendar = {};
var defaultOptions = {
    /*
        Returns the allocations in a fullcalendar compatible events feed.
        See http://fullcalendar.io/docs/event_data/events_json_feed/
    */
    feed: null,

    /*
        Returns the reservations for the current resource.
    */
    reservations: null,

    /*
        The type of the calendar. Either 'room' or 'daypass'
    */
    type: null,

    /*
        The visible time range
    */
    minTime: '07:00:00',
    maxTime: '22:00:00',

    /*
        True if the calendar may be edited (by editors/admins)
    */
    editable: false,

    /*
        Url called when a new selection is made. For example:

            selectUrl: https://example.org/on-select

        Will be called like this:

            https://example.org/on-select
                ?start=2016-02-04T2200:00.000Z
                &end=2016-02-05T2300:00.000Z
                &whole_day=no
                &view=month
    */
    selectUrl: null,

    /*
        Url which returns all available resources in the following format:
        {
            'group': [
                {
                    'name': 'name',
                    'title': 'title',
                    'url': 'url'
                }
            ]
        }
    */
    resourcesUrl: null,

    /*
        The name of the currently active resource
    */
    resourceActive: null,

    /*
        The view shown initially
    */
    view: 'month',

    /*
        The date shown initially
    */
    date: null,

    /*
        The event ids to highlight for a short while
    */
    highlights_min: null,
    highlights_max: null
};

rc.events = [
    'rc-allocations-changed',
    'rc-reservation-error',
    'rc-reservations-changed'
];

rc.passEventsToCalendar = function(calendar, target, source) {
    var cal = $(calendar);

    _.each(rc.events, function(eventName) {
        target.on(eventName, _.debounce(function(_e, data) {
            cal.trigger(eventName, [data, calendar, source]);
        }));
    });
};

rc.getFullcalendarOptions = function(options) {
    var rcOptions = $.extend(true, defaultOptions, options);

    // the fullcalendar default options
    var fcOptions = {
        allDaySlot: false,
        height: 'auto',
        events: rcOptions.feed,
        minTime: rcOptions.minTime,
        maxTime: rcOptions.maxTime,
        editable: rcOptions.editable,
        selectable: rcOptions.editable,
        defaultView: rcOptions.view,
        highlights_min: rcOptions.highlights_min,
        highlights_max: rcOptions.highlights_max,
        afterSetup: [],
        viewRenderers: [],
        eventRenderers: [],
        reservations: rcOptions.reservations,
        reservationform: rcOptions.reservationform
    };

    // the reservation calendar type definition
    var views = [];

    switch (rcOptions.type) {
        case 'daypass':
            views = ['month'];
            fcOptions.header = {
                left: 'title today prev,next',
                center: '',
                right: ''
            };
            break;
        case 'room':
            views = ['month', 'agendaWeek', 'agendaDay'];
            fcOptions.header = {
                left: 'title today prev,next',
                center: '',
                right: views.join(',')
            };
            break;
        default:
            throw new Error("Unknown reservation calendar type: " + options.type);
    }

    // select a valid default view
    if (!_.contains(views, rcOptions.view)) {
        fcOptions.defaultView = views[0];
    }

    // implements editing
    if (rcOptions.editable) {

        // create events on selection
        fcOptions.select = function(start, end, _jsevent, view) {
            var url = new Url(rcOptions.selectUrl);
            url.query.start = start.toISOString();

            if (view.name === "month") {
                url.query.end = end.subtract(1, 'days').toISOString();
                url.query.whole_day = 'yes';
                url.query.view = view.name;
            } else {
                url.query.end = end.toISOString();
                url.query.whole_day = 'no';
                url.query.view = view.name;
            }
            window.location.href = url.toString();
        };

        // edit events on drag&drop, resize
        fcOptions.eventDrop = fcOptions.eventResize = function(event, _delta, _revertFunc, _jsEvent, _ui, view) {
            var url = new Url(event.editurl);
            url.query.start = event.start.toISOString();
            url.query.end = event.end.toISOString();
            url.query.view = view.name;
            location.href = url.toString();
        };

        // make sure other code can react if events are being changed
        fcOptions.eventDragStart = fcOptions.eventResizeStart = function(event) {
            event.is_changing = true;
        };
    }

    // after event rendering
    fcOptions.eventRenderers.push(rc.renderPartitions);
    fcOptions.eventRenderers.push(rc.highlightEvents);
    fcOptions.eventRenderers.push(rc.setupEventPopups);

    fcOptions.eventAfterRender = function(event, element, view) {
        var renderers = view.calendar.options.eventRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](event, element, view);
        }
    };

    // view change rendering
    fcOptions.viewRender = function(view, element) {
        var renderers = view.calendar.options.viewRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](view, element);
        }
    };

    // history handling
    rc.setupHistory(fcOptions);

    // reservation selection
    rc.setupReservationSelect(fcOptions);

    // resource switching mechanism
    rc.setupResourceSwitch(fcOptions, rcOptions.resourcesUrl, rcOptions.resourceActive);

    // setup allocation refresh handling
    fcOptions.afterSetup.push(rc.setupAllocationsRefetch);

    // switch to the correct date after the instance has been creted
    if (rcOptions.date) {
        fcOptions.afterSetup.push(function(calendar) {
            calendar.fullCalendar('gotoDate', rcOptions.date);
        });
    }

    return fcOptions;
};

$.fn.reservationCalendar = function(options) {
    var fcOptions = rc.getFullcalendarOptions($.extend(true, defaultOptions, options));

    return this.map(function(_ix, element) {

        var calendar = $(element).fullCalendar(fcOptions);

        for (var i = 0; i < fcOptions.afterSetup.length; i++) {
            fcOptions.afterSetup[i](calendar);
        }

        return calendar;
    });
};

// handles clicks on events
rc.setupEventPopups = function(event, element, view) {
    $(element).click(function(e) {
        var calendar = $(view.el.closest('.fc'));
        rc.removeAllPopups();
        rc.showActionsPopup(calendar, element, event);
        e.preventDefault();
        return false;
    });
};

// highlight events implementation
rc.highlightEvents = function(event, element, view) {
    var min = view.calendar.options.highlights_min;
    var max = view.calendar.options.highlights_max;

    if (min === null || max === null) {
        return;
    }

    if (min <= event.id && event.id <= max) {
        $(element).addClass('highlight');
    }
};

rc.setupAllocationsRefetch = function(calendar) {
    $(window).on('rc-allocations-changed', function() {
        calendar.fullCalendar('refetchEvents');
    });
};

// sends requests through intercooler
rc.request = function(calendar, url, attribute) {
    var el = $('<a />')
        .attr(attribute, url)
        .css('display', 'none')
        .appendTo($('body'));

    Intercooler.processNodes(el);

    el.on('complete.ic', function() {
        el.remove();
    });

    var source = $(calendar).find('.has-popup');
    rc.passEventsToCalendar(calendar, el, source);

    el.click();
};

rc.delete = function(calendar, url) {
    rc.request(calendar, url, 'ic-delete-from');
};

rc.post = function(calendar, url) {
    rc.request(calendar, url, 'ic-post-to');
};

rc.reserve = function(calendar, url, start, end, quota, wholeDay) {
    url = new Url(url);
    url.query.start = start;
    url.query.end = end;
    url.query.quota = quota;
    url.query.whole_day = wholeDay && '1' || '0';

    rc.post(calendar, url.toString());
};

// popup handler implementation
rc.showActionsPopup = function(calendar, element, event) {
    var wrapper = $('<div class="reservation-actions">');
    var reservation = $('<div class="reservation-form">').appendTo(wrapper);

    if (event.actions.length > 0) {
        $('<h3 />').text(locale('Allocation')).appendTo(wrapper);
        $(event.actions.join('')).appendTo(wrapper);
    }

    ReservationForm.render(reservation.get(0), event, rc.previousReservationState, function(state) {
        rc.reserve(
            calendar,
            event.reserveurl,
            state.start,
            state.end,
            state.quota,
            state.wholeDay
        );
        $(this).closest('.popup').popup('hide');
    });

    rc.showPopup(calendar, element, wrapper);
};

rc.showErrorPopup = function(calendar, element, message) {
    rc.showPopup(calendar, element, message, 'top', ['error']);
};

rc.showPopup = function(calendar, element, content, position, extraClasses) {

    $(element).closest('.fc-event').addClass('has-popup');

    var options = {
        autoopen: true,
        tooltipanchor: element,
        type: 'tooltip',
        onopen: function() {
            rc.onPopupOpen.call(this, calendar);
        },
        onclose: function() {
            $(element).closest('.fc-event').removeClass('has-popup');
        },
        closebutton: true,
        closebuttonmarkup: '<a href="#" class="close">×</a>'
    };

    switch (position || 'right') {
        case 'top':
            options.horizontal = 'center';
            options.vertical = 'top';
            options.extraClasses = _.union(['top'], extraClasses || []);
            options.offsettop = -5;
            options.offsetleft = 20; // for some reason the popup's a bit off center
            break;
        case 'right':
            options.horizontal = 'right';
            options.vertical = 'middle';
            options.extraClasses = _.union(['right'], extraClasses || []);
            options.offsetleft = -10;
            break;
        default:
            throw Error("Unknown position: " + position);
    }

    $('<div class="popup" />').append(content).popup(options);
};

rc.onPopupOpen = function(calendar) {
    var popup = $(this);
    var options = popup.data('popupoptions');

    _.each(options.extraClasses, function(className) {
        popup.addClass(className);
    });

    var links = popup.find('a:not(.internal)');

    // hookup all links with intercool
    links.each(function(_ix, link) {
        Intercooler.processNodes($(link));
    });

    // close the popup after any click on a link
    _.each(['ic.success', 'mouseup'], function(eventName) {
        $(links).on(eventName, _.debounce(function() {
            popup.popup('hide');
        }));
    });

    // hookup the confirmation dialog
    var confirm_links = popup.find('a.confirm');
    confirm_links.confirmation();

    // pass all reservationcalendar events to the calendar
    rc.passEventsToCalendar(calendar, links, options.tooltipanchor);
};

rc.removeAllPopups = function() {
    $('.popup').popup('hide').remove();
};

// setup browser history handling
rc.setupHistory = function(fcOptions) {
    var isPopping = false;
    var isFirst = true;

    fcOptions.viewRenderers.push(function(view) {
        if (isPopping) {
            return;
        }

        var url = new Url(window.location.href);
        url.query.view = view.name;
        url.query.date = view.intervalStart.format('YYYYMMDD');

        $('a.calendar-dependent').each(function(_ix, el) {
            var dependentUrl = new Url($(el).attr('href'));
            dependentUrl.query.view = url.query.view;
            dependentUrl.query.date = url.query.date;
            $(el).attr('href', dependentUrl.toString());
        });

        var state = [
            {
                'view': view.name,
                'date': view.intervalStart
            },
            document.title + ' ' + view.title,
            url.toString()
        ];

        if (isFirst) {
            window.history.replaceState.apply(window.history, state);
            isFirst = false;
        } else {
            window.history.pushState.apply(window.history, state);
        }
    });

    fcOptions.afterSetup.push(function(calendar) {
        window.onpopstate = function(event) {
            if (event.state === null) {
                return;
            }

            isPopping = true;
            calendar.fullCalendar('changeView', event.state.view);
            calendar.fullCalendar('gotoDate', event.state.date);
            isPopping = false;
        };
    });
};

// setup the reservation selection on the right
rc.setupReservationSelect = function(fcOptions) {
    var selection = null;

    fcOptions.afterSetup.push(function(calendar) {
        var view = $(calendar).find('.fc-view-container');

        selection = $('<div class="reservation-selection"></div>')
            .insertAfter(view);
        $('<div class="clearfix"></div>').insertAfter(selection);

        calendar.fullCalendar('option', 'aspectRatio', 1.1415926);

        calendar.on('rc-reservation-error', function(_e, data, _calendar, target) {
            var event = calendar.find('.has-popup');

            if (!target || target.length === 0) {
                if (event.length !== 0) {
                    target = event;
                } else {
                    target = calendar.find('.fc-view');
                }
            }

            target = target || calendar.find('.has-popup') || calendar.find('.fc-view');
            rc.showErrorPopup(calendar, target, data.message);
        });

        calendar.on('rc-reservations-changed', function() {
            $.getJSON(fcOptions.reservations + '&ie-cache=' + (new Date()).getTime(), function(data) {
                ReservationSelection.render(
                    selection.get(0),
                    calendar,
                    data.reservations,
                    data.prediction,
                    fcOptions.reservationform
                );

                rc.loadPreviousReservationState(data.reservations);
            });
        });

        calendar.trigger('rc-reservations-changed');
    });
};

// setup the ability to switch to other resources
rc.setupResourceSwitch = function(fcOptions, resourcesUrl, active) {
    fcOptions.afterSetup.push(function(calendar) {
        var setup = function(choices) {
            var container = $(calendar).find('.fc-center');

            if (fcOptions.header.right === '') {
                container.css('float', 'right');
            }

            var lookup = {};

            var switcher = $('<select>').append(
                _.map(choices, function(resources, group) {
                    return $('<optgroup>').attr('label', group || '').append(
                        _.map(resources, function(resource) {
                            lookup[resource.name] = resource.url;

                            return $('<option>')
                                .attr('value', resource.name)
                                .attr('selected', resource.name === active)
                                .text(resource.title);
                        })
                    );
                })
            );

            switcher.change(function() {
                var url = new Url(lookup[$(this).val()]);
                url.query = (new Url(window.location.href)).query;

                window.location = url;
            });

            container.append(switcher);
        };

        $.getJSON(resourcesUrl, setup);
    });
};

// takes the loaded reservations and deduces the previous state from them
rc.loadPreviousReservationState = function(reservations) {
    if (reservations.length > 0) {
        reservations = _.sortBy(reservations, function(reservation) {
            return reservation.created;
        });

        for (var i = reservations.length - 1; i >= 0; i--) {
            if (reservations[i].time.match(/^\d{2}:\d{2} - \d{2}:\d{2}$/)) {
                rc.previousReservationState = {
                    'start': reservations[i].time.split(' - ')[0],
                    'end': reservations[i].time.split(' - ')[1]
                };

                break;
            }
        }
    } else {
        rc.previousReservationState = {};
    }
};

// renders the occupied partitions on an event
rc.renderPartitions = function(event, element, calendar) {

    if (event.is_moving) {
        return;
    }

    var free = _.template('<div style="height:<%= height %>%;" class="partition-free"></div>');
    var used = _.template('<div style="height:<%= height %>%;" class="partition-occupied"></div>');
    var partition_block = _.template('<div style="height:<%= height %>px;" class="partitions"><%= partitions %></div>');

    // build the individual partitions
    var event_partitions = rc.adjustPartitions(
        event,
        moment.duration(calendar.options.minTime).hours(),
        moment.duration(calendar.options.maxTime).hours()
    );

    var partitions = '';
    _.each(event_partitions, function(partition) {
        var reserved = partition[1];
        if (reserved === false) {
            partitions += free({height: partition[0]});
        } else {
            partitions += used({height: partition[0]});
        }
    });

    // locks the height during resizing
    var height = element.outerHeight(true);
    if (event.is_changing) {
        height = event.height;
        $(element).addClass('changing');
    } else {
        event.height = height;
    }

    // render the whole block
    var html = $(partition_block({height: height, partitions: partitions}));
    var offset = 0;
    var duration = event.end - event.start;

    html.children().each(function(ix, partition) {
        var reserved = event.partitions[ix][1];
        var percent = event.partitions[ix][0] / 100;

        if (!reserved) {
            var subevent = _.clone(event);

            subevent.start = moment(event.start + duration * offset);
            subevent.end = moment(event.start + duration * (offset + percent));
            rc.setupEventPopups(subevent, partition, calendar);
        }

        offset += percent;
    });

    $('.fc-bg', element).wrapInner(html);
};

// partitions are relative to the event. Since depending on the
// calendar only part of an event may be shown, we need to account
// for that fact. This function takes the event, and the range of
// the calendar and adjusts the partitions if necessary.
rc.adjustPartitions = function(event, min_hour, max_hour) {

    if (_.isUndefined(event.partitions)) {
        return event.partitions;
    }

    // clone the partitions
    var partitions = _.map(event.partitions, _.clone);
    var start_hour = event.start.hours();
    var end_hour = event.end.hours() === 0 ? 24 : event.end.hours();
    var duration = end_hour - start_hour;

    // if the event fits inside the calendar hours, all is ok
    if (min_hour <= start_hour && end_hour <= max_hour) {
        return partitions;
    }

    // if the whole event contains only one partition, no move will
    // change anything
    if (partitions.length <= 1) {
        return partitions;
    }

    // the event is rendered within the calendar, with the top and
    // bottom cut off. The partitions are calculated assuming the
    // event is being rendered as a whole. To adjust we cut the
    // bottom and top from the partitions and blow up the whole event.
    //
    // It made sense when I wrote the initial implementation :)
    var percentage_per_hour = 1 / duration * 100;
    var top_margin = 0, bottom_margin = 0;

    if (start_hour < min_hour) {
        top_margin = (min_hour - start_hour) * percentage_per_hour;
    }
    if (end_hour > max_hour) {
        bottom_margin = (end_hour - max_hour) * percentage_per_hour;
    }

    partitions = rc.removeMarginFromPartitions(partitions, top_margin);
    partitions.reverse();

    partitions = rc.removeMarginFromPartitions(partitions, bottom_margin);
    partitions.reverse();

    // blow up the result to 100%;
    var total = rc.sumPartitions(partitions);
    _.each(partitions, function(partition) {
        partition[0] = partition[0] / total * 100;
    });

    return partitions;
};

// remove the given margin from the top of the partitions array
// the margin is given as a percentage
rc.removeMarginFromPartitions = function(partitions, margin) {

    if (margin === 0) {
        return partitions;
    }

    var removed_total = 0;
    var original_margin = margin;

    for (var i = 0; i < partitions.length; i++) {
        if (rc.roundNumber(partitions[i][0]) >= rc.roundNumber(margin)) {
            partitions[i][0] = partitions[i][0] - margin;
            break;
        } else {
            removed_total += partitions[i][0];
            margin -= partitions[i][0];
            partitions.splice(i, 1);

            i -= 1;

            if (removed_total >= original_margin) {
                break;
            }
        }
    }

    return partitions;
};

rc.roundNumber = function(num) {
    return +Number(Math.round(num + "e+2") + "e-2");
};

rc.sumPartitions = function(partitions) {
    return _.reduce(partitions, function(running_total, p) {
        return running_total + p[0];
    }, 0);
};

/*
    Shows the list of reservations to be confirmed.
*/
ReservationSelection = React.createClass({
    handleClick: function(reservation) {
        rc.delete($(this.props.calendar), reservation.delete);
    },
    handleSubmit: function() {
        if (this.props.reservations.length) {
            window.location = this.props.reservationform;
        }
    },
    handleGotoDate: function(date) {
        this.props.calendar.fullCalendar('gotoDate', date);
    },
    handleReservePrediction: function() {
        if (this.props.prediction) {
            rc.reserve(
                this.props.calendar,
                this.props.prediction.url,
                moment(this.props.prediction.start).format('HH:mm'),
                moment(this.props.prediction.end).format('HH:mm'),
                this.props.prediction.quota,
                this.props.prediction.wholeDay
            );
        }
    },
    render: function() {
        var self = this;
        var prediction_date = this.props.prediction && moment(this.props.prediction.start).locale(window.locale.language);
        var boundGotoPredictionDate = this.props.prediction && self.handleGotoDate.bind(self, this.props.prediction.start);

        return (
            <div className="reservation-selection-inner">
                <h3>{locale("Dates")}</h3>
                {
                    this.props.reservations.length === 0 &&
                        <p>{locale("Select allocations in the calendar to reserve them")}</p>
                }
                {
                    this.props.reservations.length > 0 &&
                        <ul>{
                            _.map(this.props.reservations, function(r, ix) {
                                var boundClick = self.handleClick.bind(self, r);
                                var date = moment(r.date).locale(window.locale.language);
                                var boundGotoDate = self.handleGotoDate.bind(self, date);
                                return (
                                    <li key={ix} className="reservation">
                                        <span className="reservation-date" data-quota={r.quota}>
                                            <a onClick={boundGotoDate} title={locale('Goto date')}>
                                                {date.format('ddd LL')}
                                            </a>
                                        </span>
                                        <span className="reservation-time">{r.time}</span>
                                        {r.price && (
                                            <span className="reservation-price">
                                                {r.price.amount.toFixed(2)} {r.price.currency}
                                            </span>
                                        )}
                                        <a className="delete" onClick={boundClick}>{locale('Remove')}</a>
                                    </li>
                                );
                            })
                        }</ul>
                }
                <a onClick={self.handleSubmit} className={this.props.reservations.length === 0 && 'disabled button secondary' || 'button'}>
                    {locale("Reserve")}
                </a>

                {
                    this.props.prediction &&
                        <div className="prediction reservation">
                            <span className="reservation-date" data-quota={this.props.prediction.quota}>
                                <a onClick={boundGotoPredictionDate} title={locale('Goto date')}>
                                    {prediction_date.format('ddd LL')}
                                </a>
                            </span>
                            <span className="reservation-time">{this.props.prediction.time}</span>
                            <a className="reserve" onClick={self.handleReservePrediction}>{locale('Add Suggestion')}</a>
                        </div>
                }
            </div>
        );
    }
});

ReservationSelection.render = function(element, calendar, reservations, prediction, reservationform) {
    ReactDOM.render(
        <ReservationSelection
            calendar={calendar}
            reservations={reservations}
            reservationform={reservationform}
            prediction={prediction}
        />,
    element);
};

/*
    Allows to fine-adjust the reservation before adding it.
*/
ReservationForm = React.createClass({
    getInitialState: function() {
        var state = {
            quota: 1
        };

        // if the event is a 100% available and a full day, we pre-select
        // the whole-day button and empty the times so the user has to enter
        // a time when he switches
        if (this.props.wholeDay && this.props.fullyAvailable) {
            state.start = "";
            state.end = "";
            state.wholeDay = true;
        } else {
            state.start = this.props.start.format('HH:mm');
            state.end = this.props.end.format('HH:mm');
            state.wholeDay = false;
        }

        state.end = state.end === '00:00' && '24:00' || state.end;

        return state;
    },
    componentDidMount: function() {
        var node = $(ReactDOM.findDOMNode(this));

        // the timeout is set to 100ms because the popup will do its own focusing
        // after 50ms (we could use it, but we want to focus AND select)
        setTimeout(function() {
            node.find('input:first').focus().select();
        }, 100);
    },
    handleInputChange: function(e) {
        var state = _.extend({}, this.state);
        var name = e.target.getAttribute('name');

        switch (name) {
            case 'reserve-whole-day':
                state.wholeDay = e.target.value === 'yes';
                break;
            case 'start':
                state.start = e.target.value;
                break;
            case 'end':
                state.end = e.target.value === '00:00' && '24:00' || e.target.value;
                break;
            case 'count':
                state.quota = parseInt(e.target.value, 10);
                break;
            default:
                throw Error("Unknown input element: " + name);
        }

        this.setState(state);
    },
    handleButton: function(e) {
        var node = ReactDOM.findDOMNode(this);
        var self = this;

        $(node).find('input').each(function(_ix, el) {
            $(el).blur();
        });

        setTimeout(function() {
            self.props.onSubmit.call(node, self.state);
        }, 0);

        e.preventDefault();
    },
    handleSetPreviousTime: function(e) {
        var previousState = this.props.previousReservationState;
        var node = $(ReactDOM.findDOMNode(this));
        var inputs = node.find('[name="start"],[name="end"]');

        $(inputs[0]).val(previousState.start);
        $(inputs[1]).val(previousState.end);

        // deselect 'whole-day' if it exists
        node.find('[name="reserve-whole-day"]').filter('[value="no"]').prop('checked', true);

        // briefly highlight the inputs
        inputs.addClass('highlighted');
        setTimeout(function() {
            inputs.removeClass('highlighted');
        }, 500);

        var state = _.extend({}, this.state);
        state.start = previousState.start;
        state.end = previousState.end;
        state.wholeDay = false;

        this.setState(state);

        e.preventDefault();
    },
    handleTimeInputFocus: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.target.select();
            e.preventDefault();
        }
    },
    handleTimeInputMouseUp: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.preventDefault();
        }
    },
    handleTimeInputBlur: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.target.value = OneGov.utils.inferTime(e.target.value);
            this.handleInputChange(e);
        }
    },
    parseTime: function(date, time) {
        time = OneGov.utils.inferTime(time);

        if (!time.match(/^[0-2]{1}[0-9]{1}:?[0-5]{1}[0-9]{1}$/)) {
            return null;
        }

        var hour = parseInt(time.split(':')[0], 10);
        var minute = parseInt(time.split(':')[1], 10);

        if (hour < 0 || 24 < hour) {
            return null;
        }

        if (minute < 0 || 60 < minute) {
            return null;
        }

        date.hour(hour);
        date.minute(minute);

        return date;
    },
    isValidStart: function(start) {
        var startdate = this.parseTime(this.props.start.clone(), start);
        return startdate !== null && this.props.start <= startdate;
    },
    isValidEnd: function(end) {
        var enddate = this.parseTime(this.props.start.clone(), end);
        return enddate !== null && enddate <= this.props.end;
    },
    isValidQuota: function(quota) {
        return quota > 0 && quota <= this.props.quotaLeft;
    },
    isValidState: function() {
        if (this.props.partlyAvailable) {
            if (this.props.wholeDay && this.state.wholeDay) {
                return true;
            } else {
                return this.isValidStart(this.state.start) && this.isValidEnd(this.state.end);
            }
        } else {
            return this.isValidQuota(this.state.quota);
        }
    },
    render: function() {
        var buttonEnabled = this.isValidState();
        var showWholeDay = this.props.partlyAvailable && this.props.wholeDay;
        var showTimeRange = this.props.partlyAvailable && (!this.props.wholeDay || !this.state.wholeDay);
        var hasPreviousTimeToOffer = !_.isEmpty(this.props.previousReservationState) &&
            (
                this.props.previousReservationState.start !== this.state.start ||
                this.props.previousReservationState.end !== this.state.end
            );

        var showPreviousTime = (showTimeRange || showWholeDay) && hasPreviousTimeToOffer;
        var showQuota = !this.props.partlyAvailable;

        return (
            <form>
                {showWholeDay && (
                    <div className="field">
                        <span className="label-text">{locale("Whole day")}</span>

                        <input id="reserve-whole-day-yes"
                            name="reserve-whole-day"
                            type="radio"
                            value="yes"
                            checked={this.state.wholeDay}
                            onChange={this.handleInputChange}
                        />
                        <label htmlFor="reserve-whole-day-yes">{locale("Yes")}</label>
                        <input id="reserve-whole-day-no"
                            name="reserve-whole-day"
                            type="radio"
                            value="no"
                            checked={!this.state.wholeDay}
                            onChange={this.handleInputChange}
                        />
                        <label htmlFor="reserve-whole-day-no">{locale("No")}</label>
                    </div>
                )}

                {showTimeRange && (
                    <div className="field split">
                        <div>
                            <label htmlFor="start">{locale("From")}</label>
                            <input name="start" type="time" size="4"
                                defaultValue={this.state.start}
                                onChange={this.handleInputChange}
                                onFocus={this.handleTimeInputFocus}
                                onMouseUp={this.handleTimeInputMouseUp}
                                onBlur={this.handleTimeInputBlur}
                                className={this.isValidStart(this.state.start) && 'valid' || 'invalid'}
                            />
                        </div>
                        <div>
                            <label htmlFor="end">{locale("Until")}</label>
                            <input name="end" type="time" size="4"
                                defaultValue={this.state.end}
                                onChange={this.handleInputChange}
                                onFocus={this.handleTimeInputFocus}
                                onMouseUp={this.handleTimeInputMouseUp}
                                onBlur={this.handleTimeInputBlur}
                                className={this.isValidEnd(this.state.end) && 'valid' || 'invalid'}
                            />
                        </div>
                    </div>
                )}

                {showPreviousTime && (
                    <a href="#" onClick={this.handleSetPreviousTime} className="select-previous-time internal">
                        <i className="fa fa-chevron-circle-right" aria-hidden="true"></i>
                        <span>{this.props.previousReservationState.start}</span>
                        <span>&nbsp;-&nbsp;</span>
                        <span>{this.props.previousReservationState.end}</span>
                    </a>
                )}

                {showQuota && (
                    <div className="field">
                        <div>
                            <label htmlFor="count">{locale("Count")}</label>
                            <input name="count" type="number" size="4"
                                min="1"
                                max={this.props.quotaLeft}
                                defaultValue={this.state.quota}
                                onChange={this.handleInputChange}
                            />
                        </div>
                    </div>
                )}

                <button className={buttonEnabled && "button" || "button secondary"} disabled={!buttonEnabled} onClick={this.handleButton}>{locale("Add")}</button>
            </form>
        );
    }
});

ReservationForm.render = function(element, event, previousReservationState, onSubmit) {

    var fullyAvailable = event.partitions.length === 1 && event.partitions[0][1] === false;

    ReactDOM.render(
        <ReservationForm
            partlyAvailable={event.partlyAvailable}
            quota={event.quota}
            quotaLeft={event.quotaLeft}
            start={event.start}
            end={event.end}
            wholeDay={event.wholeDay}
            fullyAvailable={fullyAvailable}
            previousReservationState={previousReservationState}
            onSubmit={onSubmit}
        />,
    element);
};
