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
    highlights_max: null,

    /*
        Base url for exporting the current date range as a PDF
    */
    pdf_url: null
};

oc.events = [
    'oc-reservation-error',
    'oc-reservations-changed'
];

oc.overlappingEvents = {};

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
            selectable: ocOptions.editable,
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
            views = ['multiMonthYear', 'dayGridMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: 'multiMonthYear,dayGridMonth'
            };
            break;
        case 'room':
            views = ['multiMonthYear', 'dayGridMonth', 'timeGridWeek', 'timeGridDay'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: 'multiMonthYear,dayGridMonth,timeGridWeek,timeGridDay'
            };
            fcOptions.navLinks = true;
            fcOptions.weekNumbers = true;
            break;
        case 'daily-item':
            views = ['multiMonthYear', 'dayGridMonth'];
            fcOptions.headerToolbar = {
                left: 'title today prev,next',
                center: '',
                right: 'multiMonthYear,dayGridMonth'
            };
            break;
        default:
            throw new Error("Unknown reservation calendar type: " + options.type);
    }

    var list_views = [];
    for (var j = 0; j < views.length; j++) {
        var granularity = oc.getGranularity(views[j]);
        list_views[j] = 'list' + granularity[0].toUpperCase() + granularity.substring(1);
    }

    // select a valid default view
    if (!_.contains(views, ocOptions.view) && !_.contains(list_views, ocOptions.view)) {
        fcOptions.initialView = views[0];
    }

    // select initial date
    if (ocOptions.date) {
        fcOptions.initialDate = ocOptions.date;
    }

    // implements editing
    if (ocOptions.editable) {
        // add blockers on selection
        fcOptions.selectMirror = true;
        fcOptions.unselectCancel = '.popup';
        fcOptions.selectOverlap = function(event) {
            if (event.display === 'background') {
                oc.overlappingEvents[event.id] = event;
                return true;
            } else {
                oc.overlappingEvents = {};
                return false;
            }
        };
        fcOptions.selectAllow = function(info) {
            // we only know what to do if we overlap a single valid allocation
            // we only allow to add blockers in the future
            var keys = Object.keys(oc.overlappingEvents);
            if (
                keys.length === 1
                && oc.overlappingEvents[keys[0]].extendedProps.blockable
                && oc.overlappingEvents[keys[0]].extendedProps.blockurl
                && info.start >= Date.now()
            ) {
                return true;
            } else {
                oc.overlappingEvents = {};
                return false;
            }
        }
        // add blockers on selection
        fcOptions.select = function(info) {
            var keys = Object.keys(oc.overlappingEvents);
            if (keys.length !== 1) {
                // this shouldn't happen, but when it does just cancel
                oc.overlappingEvents = {};
                info.view.calendar.unselect();
                return;
            }
            var event = oc.overlappingEvents[keys[0]];
            oc.overlappingEvents = {};
            var view = info.view;
            var start = moment(info.start);
            var end = moment(info.end);
            var wholeDay = false;
            if (view.type === "dayGridMonth" || view.type === "multiMonthYear") {
                end = end.subtract(1, 'days');
                wholeDay = true;
            }
            oc.showBlockerPopup(view.calendar, $(view.calendar.el).find('.event-' + event.id).get(0) || view.calendar.el, start, end, wholeDay, event);
        }

        // edit blocker reason on click
        fcOptions.eventClick = function(info) {
            if (info.event.extendedProps.kind !== 'blocker') {
                return;
            }
            if (!info.event.extendedProps.seturl) {
                return;
            }
            oc.showBlockerEditPopup(info.view.calendar, info.el, info.event);
        };

        // edit events on drag&drop, resize
        fcOptions.eventOverlap = function(stillEvent, _movingEvent) {
            return stillEvent.display === 'background';
        };

        fcOptions.eventDrop = fcOptions.eventResize = function(info) {
            var event = info.event;
            var url = new Url(event.extendedProps.editurl);
            url.query.start = event.startStr;
            url.query.end = event.endStr;
            var calendar = $(info.el).closest('.fc').get(0) || $('.fc').get(0);
            oc.post(calendar, url.toString(), function(_evt, _elt, _status, str, _xhr) {
                info.revert();
                oc.showErrorPopup(calendar, $(calendar).find('.event-' + event.id), str);
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
    options.eventRenderers.push(oc.addDeleteBlockerHandler);

    // add id to class names so we can easily find the element
    fcOptions.eventClassNames = function(info) {
        return 'event-' + info.event.id;
    }

    // render additional content lines
    fcOptions.eventContent = function(info, h) {
        var event = info.event;
        if (event.display === 'background') {
            return null;
        }
        if (event.extendedProps.kind === 'blocker') {
            return h('div', {title: event.title}, [
                event.title,
                h('div', {class: 'delete-blocker', title: locale('Delete')}, [
                    h('i', {class: 'fa fas fa-times'})
                ])
            ]);
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
        oc.setupViewNavigation(info.view.calendar, $(info.view.calendar.el), views, ocOptions.pdf_url);
        return null;
    };

    fcOptions.eventsSet = function(events) {
        // expand visible range if necessary
        var minTime = ocOptions.minTime;
        var maxTime = ocOptions.maxTime;
        var changed = false;
        for (var i = 0; i < events.length; i++) {
            var event = events[i];
            // snap to the start of the hour
            var start = moment(event.start).startOf('hour').format('HH:mm');
            if (start < minTime) {
                minTime = start;
                changed = true;
            }
            // snap to the start of the next hour
            // unless the event ends on the hour
            var end = moment(event.end);
            end = end.minutes() === 0 ? end.format('HH:mm') : end.startOf('hour').add(1, 'hour').format('HH:mm');
            end = end == '00:00' ? '24:00' : end;
            if (end > maxTime) {
                maxTime = end;
                changed = true;
            }
        }

        if (changed) {
            this.setOption('slotMinTime', minTime);
            this.setOption('slotMaxTime', maxTime);
        }
    }

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

oc.getGranularity = function(view_name) {
    for (var i = view_name.length - 1; i >= 0; i--) {
        if (view_name[i].toUpperCase() === view_name[i]) {
            return view_name.substring(i).toLowerCase();
        }
    }
    return view_name.toLowerCase();
};

oc.setupViewNavigation = function(calendar, element, views, pdf_url) {
    var chunk = $(element).find('.fc-header-toolbar .fc-toolbar-chunk:last-child');
    var i18n = calendar.currentData.availableRawLocales[calendar.getOption('locale')];
    var granularity_group = $('<div class="fc-button-group"></div>');
    for (var i = 0; i < views.length; i++) {
        var button = $('<button type="button" class="fc-button fc-button-primary"></button>');
        var granularity = oc.getGranularity(views[i]);
        if (oc.getGranularity(calendar.view.type) === granularity) {
            button.addClass('fc-button-active');
            button.attr('aria-pressed', 'true');
        } else {
            button.attr('aria-pressed', 'false');
        }
        var label = i18n.buttonText[granularity];
        button.text(label);
        if (typeof i18n.viewHint === 'string' || i18n.viewHint instanceof String) {
            button.attr('title', i18n.viewHint.replace(/\$\d/, label));
        } else {
            button.attr('title', i18n.viewHint(label));
        }
        button.data('view', views[i]);
        button.click(function() {
            if ($(this).hasClass('fc-button-active')) {
                return false;
            }
            var view = $(this).data('view');
            if (calendar.view.type.substring(0, 4) === 'list') {
                var gran = oc.getGranularity(view);
                calendar.changeView('list' + gran[0].toUpperCase() + gran.substring(1));
            } else {
                calendar.changeView(view);
            }
            return true;
        });
        button.appendTo(granularity_group);
    }
    var view_group = $('<div class="fc-button-group"></div>');
    var calendar_btn = $('<button class="fc-button fc-button-primary"></button');
    var list_btn = $('<button class="fc-button fc-button-primary"></button');
    if (calendar.view.type.substring(0, 4) === 'list') {
        calendar_btn.attr('aria-pressed', 'false');
        list_btn.addClass('fc-button-active');
        list_btn.attr('aria-pressed', 'true');
    } else {
        calendar_btn.addClass('fc-button-active');
        calendar_btn.attr('aria-pressed', 'true');
        list_btn.attr('aria-pressed', 'false');
    }
    calendar_btn.html('<span class="fa fa-calendar fa-calendar-alt"></span>');
    calendar_btn.attr('title', locale('Calendar view'));
    calendar_btn.click(function() {
        if (calendar.view.type.substring(0, 4) !== 'list') {
            return false;
        }

        var gran = oc.getGranularity(calendar.view.type);
        for (var j = 0; j < views.length; j++) {
            if (oc.getGranularity(views[j]) === gran) {
                calendar.changeView(views[j]);
                return true;
            }
        }
        return false;
    });
    calendar_btn.appendTo(view_group);
    list_btn.html('<span class="fa fa-list"></span>');
    list_btn.attr('title', locale('List view'));
    list_btn.click(function() {
        if (calendar.view.type.substring(0, 4) === 'list') {
            return false;
        }

        var gran = oc.getGranularity(calendar.view.type);
        calendar.changeView('list' + gran[0].toUpperCase() + gran.substring(1));
        return true;
    });
    list_btn.appendTo(view_group);

    if (pdf_url) {
        var pdf_btn = $('<button class="fc-button fc-button-primary"></button');
        pdf_btn.attr('aria-pressed', 'false');
        pdf_btn.html('<span class="fa fa-file-pdf-o fa-file-pdf"></span>');
        pdf_btn.attr('title', locale("Export as PDF"));
        pdf_btn.click(function() {
            var wrapper = $('<div class="reservation-actions">');
            var form = $('<div class="reservation-form">').appendTo(wrapper);

            oc.PDFExportForm.render(
                form.get(0),
                calendar,
                function(state) {
                    var url = new Url(pdf_url || '/');
                    url.query.start = state.start;
                    url.query.end = state.end;
                    if (state.accepted) {
                        url.query.accepted = '1';
                    }
                    window.location = url.toString();
                    pdf_btn.popup('hide');
                }
            );

            oc.showPopup(calendar, pdf_btn, wrapper);
        });

        pdf_btn.appendTo(view_group);
    }

    // clear chunk
    chunk.html('');

    // append our groups
    granularity_group.appendTo(chunk);
    view_group.appendTo(chunk);
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
    if (event.extendedProps.kind !== 'reservation') {
        return;
    }

    if (view.type !== 'timeGridWeek' && view.type !== 'timeGridDay') {
        return;
    }
    $('<div class="fc-bg"></div>').insertAfter($('.fc-content', element));
};

// adds a click handler to the delete button
oc.addDeleteBlockerHandler = function(event, element, view) {
    if (event.extendedProps.kind !== 'blocker' || !event.extendedProps.deleteurl) {
        return;
    }

    $(element).find('.delete-blocker').click(function(ev) {
        ev.stopPropagation();
        $.ajax(
            event.extendedProps.deleteurl,
            {method: 'DELETE'}
        ).done(function() {
            view.calendar.refetchEvents();
        }).fail(function() {
            oc.showErrorPopup($(element).closest('.fc'), element, locale('Failed to delete'));
        });
    });
};

oc.setupReservationsRefetch = function(calendar) {
    $(window).on('oc-reservations-changed', function() {
        calendar.refetchEvents();
        calendar.unselect();
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

oc.add_blocker = function(calendar, url, start, end, reason, wholeDay) {
    url = new Url(url);
    url.query.start = start;
    url.query.end = end;
    url.query.reason = reason;
    url.query.whole_day = wholeDay && '1' || '0';

    oc.post(calendar, url.toString());
};

oc.edit_blocker = function(calendar, url, reason) {
    url = new Url(url);
    url.query.reason = reason;

    oc.post(calendar, url.toString());
};

// popup handler implementation
oc.showBlockerPopup = function(calendar, element, start, end, wholeDay, event) {
    var wrapper = $('<div class="reservation-actions">');
    var form = $('<div class="reservation-form">').appendTo(wrapper);

    // Render the blocker form
    oc.BlockerForm.render(
        form.get(0),
        start,
        end,
        wholeDay,
        event,
        function(state) {
            oc.targetEvent = $(element);
            oc.add_blocker(
                calendar,
                event.extendedProps.blockurl,
                state.start,
                state.end,
                state.reason,
                state.wholeDay
            );
            $(this).closest('.popup').popup('hide');
        }
    );

    oc.showPopup(calendar, element, wrapper);
};

oc.showBlockerEditPopup = function(calendar, element, event) {
    var wrapper = $('<div class="reservation-actions">');
    var form = $('<div class="reservation-form">').appendTo(wrapper);

    // Render the blocker form
    oc.BlockerEditForm.render(
        form.get(0),
        event,
        function(state) {
            oc.targetEvent = $(element);
            oc.edit_blocker(
                calendar,
                event.extendedProps.seturl,
                state.reason,
            );
            $(this).closest('.popup').popup('hide');
        }
    );

    oc.showPopup(calendar, element, wrapper);
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
            calendar.unselect();
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


/*
    Allows to fine-adjust the reservation blocker before adding it.
*/
oc.BlockerForm = React.createClass({
    getInitialState: function() {
        var state = {reason: null};
        if (this.props.wholeDay && this.props.wholeDayDefault && this.props.fullyAvailable) {
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
            case 'reason':
                state.reason = e.target.value || null;
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
        return startdate !== null && this.props.minStart <= startdate;
    },
    isValidEnd: function(end) {
        var enddate = this.parseTime(this.props.start.clone(), end);
        return enddate !== null && enddate <= this.props.maxEnd;
    },
    isValidState: function() {
        if (this.props.partlyAvailable) {
            if (this.props.wholeDay && this.state.wholeDay) {
                return true;
            } else {
                return this.isValidStart(this.state.start) && this.isValidEnd(this.state.end);
            }
        }
    },
    // eslint-disable-next-line complexity
    render: function() {
        var buttonEnabled = this.isValidState();
        var showWholeDay = this.props.partlyAvailable && this.props.wholeDay;
        var showTimeRange = this.props.partlyAvailable && (!this.props.wholeDay || !this.state.wholeDay);

        return (
            <form>
                <h3>{locale("Blocker")}</h3>
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

                <div className="field">
                    <div>
                        <label htmlFor="reason">{locale("Reason")}</label>
                        <input name="reason" type="text" size="30"
                            defaultValue={this.state.reason || ''}
                            onChange={this.handleInputChange}
                        />
                    </div>
                </div>

                <button className={buttonEnabled && "button" || "button secondary"} disabled={!buttonEnabled} onClick={this.handleButton}>{locale("Add")}</button>
            </form>
        );

    }
});

oc.BlockerForm.render = function(element, start, end, wholeDay, event, onSubmit) {

    var partlyAvailable = event.extendedProps.partlyAvailable;
    var fullyAvailable = event.extendedProps.fullyAvailable;
    var minStart = moment.max(moment(event.start), moment());
    var maxEnd = moment(event.end);

    ReactDOM.render(
        <oc.BlockerForm
            partlyAvailable={partlyAvailable}
            fullyAvailable={fullyAvailable}
            start={wholeDay && minStart || moment.max(start, minStart)}
            end={wholeDay && maxEnd || moment.min(end, maxEnd)}
            minStart={minStart}
            maxEnd={maxEnd}
            wholeDay={event.extendedProps.wholeDay}
            wholeDayDefault={wholeDay}
            onSubmit={onSubmit}
        />,
        element);
};


/*
    Allows to change the properties of an existing blocker.
*/
oc.BlockerEditForm = React.createClass({
    getInitialState: function() {
        return {reason: this.props.reason};
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
            case 'reason':
                state.reason = e.target.value || null;
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
    render: function() {
        return (
            <form>
                <div className="field">
                    <div>
                        <label htmlFor="reason">{locale("Reason")}</label>
                        <input name="reason" type="text" size="30"
                            defaultValue={this.state.reason || ''}
                            onChange={this.handleInputChange}
                        />
                    </div>
                </div>

                <button className="button" onClick={this.handleButton}>{locale("Update")}</button>
            </form>
        );

    }
});

oc.BlockerEditForm.render = function(element, event, onSubmit) {
    ReactDOM.render(
        <oc.BlockerEditForm
            reason={event.title}
            onSubmit={onSubmit}
        />,
        element);
};

/*
    Allows to fine-adjust the date range for the PDF export.
*/
oc.PDFExportForm = React.createClass({
    getInitialState: function() {
        return {
            start: this.props.start.format('YYYY-MM-DD'),
            end: this.props.end.format('YYYY-MM-DD'),
            accepted: true
        };
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
            case 'start':
                state.start = e.target.value;
                break;
            case 'end':
                state.end = e.target.value;
                break;
            case 'accepted':
                state.accepted = e.target.checked;
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
    },    // eslint-disable-next-line complexity
    render: function() {
        var isValid = this.state.start && this.state.end && this.state.start <= this.state.end;

        return (
            <form>
                <h3>{locale("Export as PDF")}</h3>
                <div className="field split">
                    <div>
                        <label htmlFor="start">{locale("From")}</label>
                        <input name="start" type="date" size="8"
                            defaultValue={this.state.start}
                            onChange={this.handleInputChange}
                            className={isValid && 'valid' || 'invalid'}
                        />
                    </div>
                    <div>
                        <label htmlFor="end">{locale("Until")}</label>
                        <input name="end" type="date" size="8"
                            defaultValue={this.state.end}
                            onChange={this.handleInputChange}
                            className={isValid && 'valid' || 'invalid'}
                        />
                    </div>
                </div>
                <div className="field checkbox">
                    <div>
                        <label className="label-text">
                            <input name="accepted" type="checkbox"
                                defaultChecked={this.state.accepted}
                                onChange={this.handleInputChange}
                            />
                            {locale("Accepted reservations only")}
                        </label>
                    </div>
                </div>

                <button className={isValid && "button" || "button secondary"} disabled={!isValid} onClick={this.handleButton}>{locale("Download")}</button>
            </form>
        );

    }
});

oc.PDFExportForm.render = function(element, calendar, onSubmit) {
    ReactDOM.render(
        <oc.PDFExportForm
            start={moment(calendar.view.currentStart)}
            end={moment(calendar.view.currentEnd).subtract(1, 'day')}
            onSubmit={onSubmit}
        />,
        element);
};

