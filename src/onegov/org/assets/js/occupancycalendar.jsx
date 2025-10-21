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
        oc.setupViewNavigation(info.view.calendar, $(info.view.calendar.el), views, ocOptions.pdf_url);
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
                    window.location = url.toString();
                    pdf_btn.popup('hide');
                }
            );

            rc.showPopup(calendar, pdf_btn, wrapper);
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

/*
    Allows to fine-adjust the date range for the PDF export.
*/
oc.PDFExportForm = React.createClass({
    getInitialState: function() {
        return {
            start: this.props.start.format('YYYY-MM-DD'),
            end: this.props.end.format('YYYY-MM-DD')
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

