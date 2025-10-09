/*
    The reservation calendar extends fullcalendar adding methods to allocate
    dates, select and then reserve them.
*/

var rc = $.reservationCalendar = {};
rc.defaultOptions = {
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
                &view=dayGridMonth
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
    view: 'dayGridMonth',

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

rc.targetEvent = null;

rc.passEventsToCalendar = function(calendar, target, source) {
    var cal = $(calendar);

    _.each(rc.events, function(eventName) {
        target.on(eventName, _.debounce(function(_e, data) {
            cal.trigger(eventName, [data, calendar, source]);
        }));
    });
};

rc.getFullcalendarOptions = function(rcExtendOptions) {
    var rcOptions = $.extend(true, rc.defaultOptions, rcExtendOptions);

    // contains both base options and extended options
    // extended options will be available on the calendar
    // object via calendar.exOptions
    var options = {
        // the fullcalendar default options
        fc: {
            allDaySlot: false,
            height: 'auto',
            events: rcOptions.feed,
            slotMinTime: rcOptions.minTime,
            slotMaxTime: rcOptions.maxTime,
            editable: rcOptions.editable,
            selectable: rcOptions.editable,
            initialView: rcOptions.view,
            locale: window.locale.language,
            multiMonthMaxColumns: 1
        },
        highlights_min: rcOptions.highlights_min,
        highlights_max: rcOptions.highlights_max,
        afterSetup: [],
        viewRenderers: [],
        eventRenderers: [],
        reservations: rcOptions.reservations,
        reservationform: rcOptions.reservationform
    };

    var fcOptions = options.fc;

    // the reservation calendar type definition
    var views = [];

    switch (rcOptions.type) {
        case 'daypass':
            views = ['dayGridMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: ''
            };
            break;
        case 'room':
            views = ['multiMonthYear', 'dayGridMonth', 'timeGridWeek', 'timeGridDay'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: views.join(',')
            };
            fcOptions.navLinks = true;
            fcOptions.weekNumbers = true;
            break;
        case 'daily-item':
            views = ['dayGridMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: ''
            };
            break;
        default:
            throw new Error("Unknown reservation calendar type: " + options.type);
    }

    // select a valid default view
    if (!_.contains(views, rcOptions.view)) {
        fcOptions.initialView = views[0];
    }

    // select initial date
    if (rcOptions.date) {
        fcOptions.initialDate = rcOptions.date;
    }

    // implements editing
    if (rcOptions.editable) {

        // create events on selection
        fcOptions.select = function(info) {
            var view = info.view;
            var url = new Url(rcOptions.selectUrl);
            url.query.start = info.startStr;

            if (view.type === "dayGridMonth" || view.type === "multiMonthYear") {
                var end = moment(info.end);
                url.query.end = end.subtract(1, 'days').format('YYYY-MM-DD');
                url.query.whole_day = 'yes';
                url.query.view = view.type;
            } else {
                url.query.end = info.endStr;
                url.query.whole_day = 'no';
                url.query.view = view.type;
            }
            window.location.href = url.toString();
        };

        // edit events on drag&drop, resize
        fcOptions.eventDrop = fcOptions.eventResize = function(info) {
            var event = info.event;
            var url = new Url(event.extendedProps.editurl);
            url.query.start = event.startStr;
            url.query.end = event.endStr;
            url.query.view = info.view.type;
            location.href = url.toString();
        };

        // make sure other code can react if events are being changed
        fcOptions.eventDragStart = fcOptions.eventResizeStart = function(info) {
            info.event.is_changing = true;
        };
    }

    // after event rendering
    options.eventRenderers.push(rc.renderPartitions);
    options.eventRenderers.push(rc.highlightEvents);
    options.eventRenderers.push(rc.setupEventPopups);

    // render additional content lines
    fcOptions.eventContent = function(info, h) {
        var event = info.event;
        var lines = event.title.split('\n');
        var content = [];
        for (var i = 0; i < lines.length; i++) {
            if (i !== 0) {
                content[i * 2 - 1] = h('br');
            }
            content[i * 2] = lines[i];
        }
        return h('span', {class: 'fc-title'}, content);
    };

    fcOptions.eventDidMount = function(info) {
        var renderers = options.eventRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](info.event, $(info.el), info.view);
        }
    };

    // view change rendering
    fcOptions.viewClassNames = function(info) {
        var renderers = options.viewRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](info.view, $(info.el));
        }
        return null;
    };

    // history handling
    rc.setupHistory(options);

    // reservation selection
    rc.setupReservationSelect(options);

    // resource switching mechanism
    rc.setupResourceSwitch(options, rcOptions.resourcesUrl, rcOptions.resourceActive);

    // setup allocation refresh handling
    options.afterSetup.push(rc.setupAllocationsRefetch);

    // setup date picker
    options.afterSetup.push(rc.setupDatePicker);

    return options;
};

$.fn.reservationCalendar = function(extendOptions) {
    var options = rc.getFullcalendarOptions(extendOptions);

    return this.map(function(_ix, element) {

        var calendar = new FullCalendar.Calendar(element, options.fc);
        calendar.exOptions = options;

        calendar.render();

        for (var i = 0; i < options.afterSetup.length; i++) {
            options.afterSetup[i](calendar, element);
        }

        return calendar;
    });
};

// handles clicks on events
rc.setupEventPopups = function(event, element) {
    $(element).click(function(e) {
        var calendar = $(element).closest('.fc');
        rc.removeAllPopups();
        rc.showActionsPopup(calendar, element, event);
        e.preventDefault();
        return false;
    });
};

// show date picker when clicking on title
rc.setupDatePicker = function(calendar, element) {
    var title = $(element).find('.fc-header-toolbar .fc-toolbar-title');
    var input = $(
        '<input type="text" name="date" tabindex="-1" aria-hidden="true"/>'
    ).css({
        visibility: 'hidden',
        width: 0,
        height: 0,
        border: 0,
        margin: 0,
        padding: 0
    }).datetimepicker({
        allowBlank: true,
        timepicker: false,
        format: 'Y-m-d',
        dayOfWeekStart: 1,
        lang: window.locale.language,
        closeOnDateSelect: true,
        onSelectDate: function(ct, _$i) {
            calendar.gotoDate(ct);
            rc.setHistory(ct, calendar.view);
        },
        onShow: function(_ct, $i) {
            this.setOptions({value: $i.val()});
            setTimeout(function() {
                $('.xdsoft_datetimepicker').trigger('afterOpen.xdsoft');
            }, 50);
        }
    });
    var icon = $(
        '<span class="fa fa-calendar fa-calendar-alt absolute"></span>'
    ).css('margin-left', '.5rem');
    input.unbind();
    title.append(icon);
    title.append(input);
    title.click(function() {
        input.val(moment(calendar.getDate()).format('YYYY-MM-DD'));
        input.datetimepicker('show');
    }).on('mouseenter', function() {
        title.css('cursor', 'pointer');
    }).on('mouseleave', function() {
        title.css('cursor', '');
    });
};

// highlight events implementation
rc.highlightEvents = function(event, element, view) {
    var min = view.calendar.exOptions.highlights_min;
    var max = view.calendar.exOptions.highlights_max;

    if (min === null || max === null) {
        return;
    }

    if (min <= event.id && event.id <= max) {
        $(element).addClass('highlight');
    }
};

rc.setupAllocationsRefetch = function(calendar) {
    $(window).on('rc-allocations-changed', function() {
        calendar.refetchEvents();
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
        rc.targetEvent = null;
    });

    var source = rc.targetEvent || $(calendar).find('.has-popup');
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

// eslint-disable-next-line complexity
rc.shouldRenderReservationForm = function(event, previousReservationState) {
    const showWholeDay = event.extendedProps.partlyAvailable && event.extendedProps.wholeDay;
    const showTimeRange = event.extendedProps.partlyAvailable && (!event.extendedProps.wholeDay || !(event.state && event.state.wholeDay));
    const hasPreviousTimeToOffer = !_.isEmpty(previousReservationState) &&
        (
            previousReservationState.start !== moment(event.start).format('HH:mm') ||
            previousReservationState.end !== moment(event.end).format('HH:mm')
        );
    const showPreviousTime = (showTimeRange || showWholeDay) && hasPreviousTimeToOffer;
    const showQuota = !event.extendedProps.partlyAvailable && (event.extendedProps.quotaLeft > 0) && (event.extendedProps.quota > 1);

    // Determine if any fields need to be rendered
    return (
        showWholeDay ||
        showTimeRange ||
        showPreviousTime ||
        showQuota
    );
};

// popup handler implementation
rc.showActionsPopup = function(calendar, element, event) {
    var wrapper = $('<div class="reservation-actions">');
    var reservation = $('<div class="reservation-form">').appendTo(wrapper);

    if (event.extendedProps.actions.length > 0) {
        $('<h3 />').text(locale('Allocation')).appendTo(wrapper);
        $(event.extendedProps.actions.join('')).appendTo(wrapper);
    }

    // Check if the reservation form needs to be rendered
    if (!event.extendedProps.actions.length && !rc.shouldRenderReservationForm(event, rc.previousReservationState)) {
        // Directly submit the reservation if no fields or actions are present
        rc.targetEvent = $(element);
        rc.reserve(
            calendar,
            event.extendedProps.reserveurl,
            moment(event.start).format('HH:mm'),
            moment(event.end).format('HH:mm'),
            event.extendedProps.quotaLeft,
            event.extendedProps.wholeDay
        );
        return;
    }

    // Render the reservation form if needed
    ReservationForm.render(
        reservation.get(0),
        event,
        rc.previousReservationState,
        function(state) {
            rc.targetEvent = $(element);
            rc.reserve(
                calendar,
                event.extendedProps.reserveurl,
                state.start,
                state.end,
                state.quota,
                state.wholeDay
            );
            $(this).closest('.popup').popup('hide');
        }
    );

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
            setTimeout(function() {
                $(window).trigger('resize');
            }, 0);
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

rc.isFirstHistoryEntry = true;

rc.setHistory = function(date, view) {
    var url = new Url(window.location.href);
    url.query.view = view.type;
    url.query.date = moment(date).format('YYYYMMDD');

    $('a.calendar-dependent').each(function(_ix, el) {
        var dependentUrl = new Url($(el).attr('href'));
        dependentUrl.query.view = url.query.view;
        dependentUrl.query.date = url.query.date;
        $(el).attr('href', dependentUrl.toString());
    });

    var state = [
        {
            'view': view.type,
            'date': date
        },
        document.title + ' ' + view.title,
        url.toString()
    ];

    if (rc.isFirstHistoryEntry) {
        window.history.replaceState.apply(window.history, state);
        rc.isFirstHistoryEntry = false;
    } else {
        window.history.pushState.apply(window.history, state);
    }
};

// setup browser history handling
rc.setupHistory = function(options) {
    var isPopping = false;

    options.viewRenderers.push(function(view) {
        if (isPopping) {
            return;
        }

        var start = view.currentStart;
        if (view.type === 'multiMonthYear') {
            // instead use getDate and truncate to the current month
            var current = view.calendar.getDate();
            start = moment({
                year: current.getFullYear(),
                month: current.getMonth(),
                day: 1
            }).toDate();
        }

        rc.setHistory(start, view);
    });

    options.afterSetup.push(function(calendar) {
        window.onpopstate = function(event) {
            if (event.state === null) {
                return;
            }

            isPopping = true;
            calendar.changeView(event.state.view);
            calendar.gotoDate(event.state.date);
            isPopping = false;
        };
    });
};

// add ie-cache busting to url
rc.bustIECache = function(originalUrl) {
    var url = new Url(originalUrl);
    url.query['ie-cache'] = (new Date()).getTime();
    return url.toString();
};

// setup the reservation selection on the right
rc.setupReservationSelect = function(options) {
    var selection = null;

    options.afterSetup.push(function(calendar, element) {
        var view = $(element).find('.fc-view');

        selection = $('<div class="reservation-selection"></div>')
            .insertAfter(view);
        $('<div class="clearfix"></div>').insertAfter(selection);

        calendar.setOption('aspectRatio', 1.2);

        $(element).on('rc-reservation-error', function(_e, data, _calendar, target) {
            var event = $(element).find('.has-popup');

            if (!target || target.length === 0) {
                if (event.length !== 0) {
                    target = event;
                } else {
                    target = view;
                }
            }

            target = target || $(element).find('.has-popup') || view;
            rc.showErrorPopup(calendar, target, data.message);
        });

        $(element).on('rc-reservations-changed', function() {
            $.getJSON(rc.bustIECache(options.reservations), function(data) {
                ReservationSelection.render(
                    selection.get(0),
                    $(element),
                    data.reservations,
                    data.prediction,
                    options.reservationform
                );

                rc.loadPreviousReservationState(data.reservations);
            });
        });

        $(element).trigger('rc-reservations-changed');
    });
};

// setup the ability to switch to other resources
rc.setupResourceSwitch = function(options, resourcesUrl, active) {
    options.afterSetup.push(function(_calendar, element) {
        var setup = function(choices) {
            var container = $(element).find('.fc-toolbar-chunk').eq(1);

            if (options.fc.headerToolbar.right === '') {
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
rc.renderPartitions = function(event, element, view) {

    if (event.is_moving) {
        return;
    }

    if (view.type !== 'timeGridWeek' && view.type !== 'timeGridDay') {
        return;
    }

    var calendar = view.calendar;
    var free = _.template('<div style="height:<%= height %>%;" class="partition-free"></div>');
    var used = _.template('<div style="height:<%= height %>%;" class="partition-occupied"></div>');

    // build the individual partitions
    var event_partitions = rc.adjustPartitions(
        event,
        moment.duration(calendar.getOption('slotMinTime')).hours(),
        moment.duration(calendar.getOption('slotMaxTime')).hours()
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
    var html = $(partitions);
    var offset = 0;
    var start = moment(event.start);
    var duration = moment(event.end) - start;

    html.each(function(ix, partition) {
        var reserved = event.extendedProps.partitions[ix][1];
        var percent = event.extendedProps.partitions[ix][0] / 100;

        if (!reserved) {
            var subevent = _.clone(event);

            subevent.start = moment(start + duration * offset);
            subevent.end = moment(start + duration * (offset + percent));
            subevent.extendedProps = event.extendedProps;
            rc.setupEventPopups(subevent, partition);
        }

        offset += percent;
    });

    $('<div class="fc-bg"></div>').wrapInner(html).insertAfter($('.fc-event-main', element));
};

// partitions are relative to the event. Since depending on the
// calendar only part of an event may be shown, we need to account
// for that fact. This function takes the event, and the range of
// the calendar and adjusts the partitions if necessary.
rc.adjustPartitions = function(event, min_hour, max_hour) {

    if (_.isUndefined(event.extendedProps.partitions)) {
        return event.extendedProps.partitions;
    }

    // clone the partitions
    var partitions = _.map(event.extendedProps.partitions, _.clone);
    var start_hour = moment(event.start).hours();
    var end_hour = moment(event.end).hours() === 0 ? 24 : moment(event.end).hours();
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
                    <p>{locale("Select one ore more allocations in the calendar to reserve them.")}</p>
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
                                            <a onClick={boundGotoDate} title={locale('Goto date')} role="link">
                                                {date.format('ddd LL')}
                                            </a>
                                            {r.warning && (
                                                <span className="reservation-warning" title={r.warning}>
                                                    <i className="fa fa-clock-o" aria-hidden="true" />
                                                </span>
                                            )}
                                        </span>
                                        <span className="reservation-time">{r.time}</span>
                                        {r.price && (
                                            <span className="reservation-price">
                                                {r.price.amount.toFixed(2)} {r.price.currency}
                                            </span>
                                        )}
                                        <a className="delete" onClick={boundClick} role="button">{locale('Remove')}</a>
                                    </li>
                                );
                            })
                        }</ul>
                }
                <a onClick={self.handleSubmit} role="button" className={this.props.reservations.length === 0 && 'disabled button secondary' || 'button'}>
                    {locale("Reserve")}
                </a>

                {
                    this.props.prediction &&
                        <div className="prediction reservation">
                            <span className="reservation-date" data-quota={this.props.prediction.quota}>
                                <a onClick={boundGotoPredictionDate} title={locale('Goto date')} role="link">
                                    {prediction_date.format('ddd LL')}
                                </a>
                            </span>
                            <span className="reservation-time">{this.props.prediction.time}</span>
                            <a className="reserve" onClick={self.handleReservePrediction} role="button">{locale('Add Suggestion')}</a>
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
    // eslint-disable-next-line complexity
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
                        <i className="fa fa-chevron-circle-right" aria-hidden="true" />
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

    var fullyAvailable = event.extendedProps.partitions.length === 1 && event.extendedProps.partitions[0][1] === false;

    ReactDOM.render(
        <ReservationForm
            partlyAvailable={event.extendedProps.partlyAvailable}
            quota={event.extendedProps.quota}
            quotaLeft={event.extendedProps.quotaLeft}
            start={moment(event.start)}
            end={moment(event.end)}
            wholeDay={event.extendedProps.wholeDay}
            fullyAvailable={fullyAvailable}
            previousReservationState={previousReservationState}
            onSubmit={onSubmit}
        />,
        element);
};
