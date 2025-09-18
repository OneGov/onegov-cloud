/*
    The occupancy calendar extends fullcalendar.
*/

var oc = $.occupancyCalendar = {};
oc.defaultOptions = {
    /*
        Returns the reservations in a fullcalendar compatible events feed.
        See http://fullcalendar.io/docs/event_data/events_json_feed/
    */
    feed: null,

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

oc.events = [
    'oc-reservation-error',
    'oc-reservations-changed'
];

oc.passEventsToCalendar = function(calendar, target) {
    var cal = $(calendar);

    _.each(oc.events, function(eventName) {
        target.on(eventName, _.debounce(function(_e, data) {
            cal.trigger(eventName, [data, calendar]);
        }));
    });
};

oc.getFullcalendarOptions = function(ocExtendOptions) {
    var ocOptions = $.extend(true, oc.defaultOptions, ocExtendOptions);

    // the fullcalendar default options
    var options = {
        fc: {
            allDaySlot: false,
            height: 'auto',
            events: ocOptions.feed,
            slotMinTime: ocOptions.minTime,
            slotMaxTime: ocOptions.maxTime,
            snapDuration: '00:15',
            editable: ocOptions.editable,
            eventResizableFromStart: ocOptions.editable,
            selectable: false,
            initialView: ocOptions.view,
            locale: window.locale.language,
            multiMonthMaxColumns: 1
        },
        highlights_min: ocOptions.highlights_min,
        highlights_max: ocOptions.highlights_max,
        afterSetup: [],
        viewRenderers: [],
        eventRenderers: []
    };

    var fcOptions = options.fc;

    // the reservation calendar type definition
    var views = [];

    switch (ocOptions.type) {
        case 'daypass':
            views = ['dayGridMonth', 'listMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: 'month listMonth'
            };
            break;
        case 'room':
            views = ['multiMonthYear', 'dayGridMonth', 'timeGridWeek', 'timeGridDay', 'listMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: 'multiMonthYear,dayGridMonth,timeGridWeek,timeGridDay listMonth'
            };
            fcOptions.navLinks = true;
            fcOptions.weekNumbers = true;
            break;
        case 'daily-item':
            views = ['month', 'listMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: 'month listMonth'
            };
            break;
        default:
            throw new Error("Unknown reservation calendar type: " + options.type);
    }

    // select a valid default view
    if (!_.contains(views, ocOptions.view)) {
        fcOptions.initialView = views[0];
    }

    // select initial date
    if (ocOptions.date) {
        fcOptions.initialDate = ocOptions.date;
    }

    // implements editing
    if (ocOptions.editable) {

        fcOptions.eventOverlap = function(stillEvent, _movingEvent) {
            return stillEvent.display === 'background';
        };

        // edit events on drag&drop, resize
        fcOptions.eventDrop = fcOptions.eventResize = function(info) {
            var event = info.event;
            var url = new Url(event.extendedProps.editurl);
            url.query.start = event.startStr;
            url.query.end = event.endStr;
            var calendar = $(info.el).closest('.fc');
            oc.post(calendar, url.toString(), function(_evt, _elt, _status, str, _xhr) {
                info.revert();
                oc.showErrorPopup(calendar, calendar.find('.event-' + event.id), str);
            });
        };

        // make sure other code can react if events are being changed
        fcOptions.eventDragStart = fcOptions.eventResizeStart = function(info) {
            info.event.is_changing = true;
        };
    }

    // after event rendering
    options.eventRenderers.push(oc.highlightEvents);
    options.eventRenderers.push(oc.addEventBackground);

    // render additional content lines
    fcOptions.eventContent = function(info, h) {
        var event = info.event;
        if (event.display === 'background') {
            return null;
        }
        var lines = event.title.split('\n');
        var attrs = {class: 'fc-title'};
        // truncate title when it doesn't fit
        if (info.view.type === 'timeGridWeek' || info.view.type === 'timeGridDay') {
            attrs.title = event.title;
            var max_lines = Math.max(1, Math.floor(moment(event.end).diff(moment(event.start), 'minutes') / 30));
            lines = lines.slice(0, max_lines);
        } else if (info.view.type === 'multiMonthYear') {
            attrs.title = event.title;
        }
        var content = [];
        for (var i = 0; i < lines.length; i++) {
            if (i !== 0) {
                content.push(h('br'));
            }
            content.push(lines[i]);
        }
        return h('div', {class: 'fc-content'}, h('span', attrs, content));
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
    oc.setupHistory(options);

    // setup allocation refresh handling
    options.afterSetup.push(oc.setupReservationsRefetch);

    // setup date picker
    options.afterSetup.push(oc.setupDatePicker);

    return options;
};

$.fn.occupancyCalendar = function(extendOptions) {
    var options = oc.getFullcalendarOptions(extendOptions);

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

// show date picker when clicking on title
oc.setupDatePicker = function(calendar, element) {
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
            oc.setHistory(ct, calendar.view);
        },
        onShow: function(_ct, $i) {
            this.setOptions({value: $i.val()});
            setTimeout(function() {
                $('.xdsoft_datetimepicker').trigger('afterOpen.xdsoft');
            }, 50);
        }
    });
    var icon = $(
        '<span class="fa fa-calendar fa-calendar-alt"></span>'
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
oc.highlightEvents = function(event, element, view) {
    var min = view.calendar.exOptions.highlights_min;
    var max = view.calendar.exOptions.highlights_max;

    if (min === null || max === null) {
        return;
    }

    if (min <= event.id && event.id <= max) {
        $(element).addClass('highlight');
    }
};

// adds a fc-bg div to the views where we need it
oc.addEventBackground = function(event, element, view) {
    if (event.display === 'background') {
        return;
    }

    if (view.type !== 'timeGridWeek' && view.type !== 'timeGridDay') {
        return;
    }
    $('<div class="fc-bg"></div>').insertAfter($('.fc-content', element));
};

oc.setupReservationsRefetch = function(calendar) {
    $(window).on('oc-reservations-changed', function() {
        calendar.refetchEvents();
    });
};

// sends requests through intercooler
oc.request = function(calendar, url, attribute, onerror) {
    var el = $('<a />')
        .attr(attribute, url)
        .css('display', 'none')
        .appendTo($('body'));

    Intercooler.processNodes(el);

    el.on('complete.ic', function() {
        el.remove();
    });

    if (onerror !== undefined) {
        el.on('success.ic', function(evt, elt, strdata, status, xhr) {
            var data = JSON.parse(strdata);
            if (data.success === false) {
                onerror(evt, elt, status, data.message, xhr);
            }
        });
        el.on('error.ic', onerror);
    }

    oc.passEventsToCalendar(calendar, el);

    el.click();
};

oc.post = function(calendar, url, onerror) {
    oc.request(calendar, url, 'ic-post-to', onerror);
};

oc.showErrorPopup = function(calendar, element, message) {
    oc.showPopup(calendar, element, message, 'top', ['error']);
};

oc.showPopup = function(calendar, element, content, position, extraClasses) {

    $(element).closest('.fc-event').addClass('has-popup');

    var options = {
        autoopen: true,
        tooltipanchor: element,
        type: 'tooltip',
        onopen: function() {
            oc.onPopupOpen.call(this, calendar);
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

oc.onPopupOpen = function(calendar) {
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
    oc.passEventsToCalendar(calendar, links, options.tooltipanchor);
};

oc.removeAllPopups = function() {
    $('.popup').popup('hide').remove();
};

oc.isFirstHistoryEntry = true;

oc.setHistory = function(date, view) {
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

    if (oc.isFirstHistoryEntry) {
        window.history.replaceState.apply(window.history, state);
        oc.isFirstHistoryEntry = false;
    } else {
        window.history.pushState.apply(window.history, state);
    }
};

// setup browser history handling
oc.setupHistory = function(options) {
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

        oc.setHistory(start, view);
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
oc.bustIECache = function(originalUrl) {
    var url = new Url(originalUrl);
    url.query['ie-cache'] = (new Date()).getTime();
    return url.toString();
};
