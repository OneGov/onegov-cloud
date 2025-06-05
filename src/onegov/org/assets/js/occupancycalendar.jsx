/*
    The occupancy calendar extends fullcalendar.
*/

var oc = $.occupancyCalendar = {};
var defaultOptions = {
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

oc.getFullcalendarOptions = function(options) {
    var ocOptions = $.extend(true, defaultOptions, options);

    // the fullcalendar default options
    var fcOptions = {
        allDaySlot: false,
        height: 'auto',
        events: ocOptions.feed,
        minTime: ocOptions.minTime,
        maxTime: ocOptions.maxTime,
        editable: ocOptions.editable,
        selectable: false,
        defaultView: ocOptions.view,
        highlights_min: ocOptions.highlights_min,
        highlights_max: ocOptions.highlights_max,
        afterSetup: [],
        viewRenderers: [],
        eventRenderers: [],
        locale: window.locale.language
    };

    // the reservation calendar type definition
    var views = [];

    switch (ocOptions.type) {
        case 'daypass':
            views = ['month', 'listMonth'];
            fcOptions.header = {
                left: 'title today prev,next',
                center: '',
                right: 'month listMonth'
            };
            break;
        case 'room':
            views = ['month', 'agendaWeek', 'agendaDay', 'listMonth', 'listWeek', 'listDay'];
            fcOptions.header = {
                left: 'title today prev,next',
                center: '',
                right: 'month,agendaWeek,agendaDay listMonth'
            };
            fcOptions.navLinks = true;
            fcOptions.weekNumbers = true;
            break;
        case 'daily-item':
            views = ['month', 'listMonth'];
            fcOptions.header = {
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
        fcOptions.defaultView = views[0];
    }

    // implements editing
    if (ocOptions.editable) {

        fcOptions.eventOverlap = function(stillEvent, _movingEvent) {
            return stillEvent.rendering === 'background';
        };

        // edit events on drag&drop, resize
        fcOptions.eventDrop = fcOptions.eventResize = function(event, _delta, revertFunc, _jsEvent, _ui, view) {
            var url = new Url(event.editurl);
            url.query.start = event.start.toISOString();
            url.query.end = event.end.toISOString();
            var calendar = $(view.el.closest('.fc'));
            oc.post(calendar, url.toString(), function(_evt, _elt, _status, str, _xhr) {
                revertFunc();
                oc.showErrorPopup(calendar, calendar.find('.event-' + event.id), str);
            });
        };

        // make sure other code can react if events are being changed
        fcOptions.eventDragStart = fcOptions.eventResizeStart = function(event) {
            event.is_changing = true;
        };
    }

    // after event rendering
    fcOptions.eventRenderers.push(oc.highlightEvents);

    // truncate title when it doesn't fit
    fcOptions.eventRender = function(event, element, view) {
        if (view.name !== 'agendaWeek' && view.name !== 'agendaDay') {
            return;
        }
        if (event.rendering === 'background') {
            return;
        }
        var title = element.find('.fc-title');
        var lines = title.html().split('<br>');
        var max_lines = Math.max(1, Math.round(event.end.diff(event.start, 'minutes') / 30));
        if (lines.length > max_lines) {
            element.attr('title', event.title);
            title.html(lines.slice(0, max_lines).join('<br>'));
        }
    };

    fcOptions.eventAfterRender = function(event, element, view) {
        var renderers = view.options.eventRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](event, element, view);
        }
    };

    // view change rendering
    fcOptions.viewRender = function(view, element) {
        oc.setupDatePicker(view, element);
        var renderers = view.options.viewRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](view, element);
        }
    };

    // history handling
    oc.setupHistory(fcOptions);

    // setup allocation refresh handling
    fcOptions.afterSetup.push(oc.setupReservationsRefetch);

    // switch to the correct date after the instance has been created
    if (ocOptions.date) {
        fcOptions.afterSetup.push(function(calendar) {
            calendar.fullCalendar('gotoDate', ocOptions.date);
        });
    }

    return fcOptions;
};

$.fn.occupancyCalendar = function(options) {
    var fcOptions = oc.getFullcalendarOptions($.extend(true, defaultOptions, options));

    return this.map(function(_ix, element) {

        var calendar = $(element).fullCalendar(fcOptions);

        for (var i = 0; i < fcOptions.afterSetup.length; i++) {
            fcOptions.afterSetup[i](calendar);
        }

        return calendar;
    });
};

// show date picker when clicking on title
oc.setupDatePicker = function(view, _element) {
    var calendar = $(view.el.closest('.fc'));
    var title = calendar.find('.fc-header-toolbar .fc-left h2');
    var input = $(
        '<input type="text" tabindex="-1" aria-hidden="true"/>'
    ).css({
        visibility: 'hidden',
        width: 0,
        height: 0,
        border: 0
    }).datetimepicker({
        allowBlank: true,
        timepicker: false,
        format: 'Y-m-d',
        dayOfWeekStart: 1,
        lang: window.locale.language,
        closeOnDateSelect: true,
        onSelectDate: function(ct, _$i) {
            calendar.fullCalendar('gotoDate', ct);
        },
        onShow: function(_ct, $i) {
            this.setOptions({value: $i.val()});
            setTimeout(function() {
                $('.xdsoft_datetimepicker').trigger('afterOpen.xdsoft');
            }, 50);
        }
    });
    input.unbind();
    title.append(input);
    title.click(function() {
        input.val(calendar.fullCalendar('getDate').format('YYYY-MM-DD'));
        input.datetimepicker('show');
    }).on('mouseenter', function() {
        title.css('cursor', 'pointer');
    }).on('mouseleave', function() {
        title.css('cursor', '');
    });
};

// highlight events implementation
oc.highlightEvents = function(event, element, view) {
    var min = view.options.highlights_min;
    var max = view.options.highlights_max;

    if (min === null || max === null) {
        return;
    }

    if (min <= event.id && event.id <= max) {
        $(element).addClass('highlight');
    }
};

oc.setupReservationsRefetch = function(calendar) {
    $(window).on('oc-reservations-changed', function() {
        calendar.fullCalendar('refetchEvents');
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

// setup browser history handling
oc.setupHistory = function(fcOptions) {
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

// add ie-cache busting to url
oc.bustIECache = function(originalUrl) {
    var url = new Url(originalUrl);
    url.query['ie-cache'] = (new Date()).getTime();
    return url.toString();
};
