var new_select_handler = function(baseurl) {
    return function(start, end, _jsevent, view) {
        var url = new Url(baseurl);
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
};

var edit_handler = function(event) {
    var url = newUrl(event.editurl);
    url.query.start = event.start.toISOString();
    url.query.end = event.end.toISOString();
    location.href = url.toString();
};

var spawn_popup = function(event, element) {

    $(element).addClass('has-popup');

    var popup_content = $('<div class="popup" />')
        .append($(event.actions.join('')));

    popup_content.popup({
        'autoopen': true,
        'blur': true,
        'horizontal': 'right',
        'offsetleft': -10,
        'tooltipanchor': element,
        'transition': null,
        'type': 'tooltip',
        'onopen': function() {
            var popup = $(this);

            // hookup the confirmation dialog
            var confirm_links = popup.find('a.confirm');
            Intercooler.processNodes(confirm_links);
            confirm_links.confirmation();
            $(confirm_links).on('success.ic', function() {
                $('.calendar').fullCalendar('refetchEvents');
            });

            // any link clicked will close the popup
            popup.find('a').click(function() {
                popup.popup('hide');
            });
        },
        'onclose': function() {
            $(element).removeClass('has-popup');
        },
        'detach': true
    });
};

var sum_partitions = function(partitions) {
    return _.reduce(partitions, function(running_total, p) {
        return running_total + p[0];
    }, 0);
};

var round_number = function(num) {
    return +Number(Math.round(num + "e+2") + "e-2");
};

// remove the given margin from the top of the partitions array
// the margin is given as a percentage
var remove_margin_from_partitions = function(partitions, margin) {

    if (margin === 0) {
        return partitions;
    }

    var removed_total = 0;
    var original_margin = margin;

    for (var i = 0; i < partitions.length; i++) {
        if (round_number(partitions[i][0]) >= round_number(margin)) {
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

// partitions are relative to the event. Since depending on the
// calendar only part of an event may be shown, we need to account
// for that fact. This function takes the event, and the range of
// the calendar and adjusts the partitions if necessary.
var adjust_partitions = function(event, min_hour, max_hour) {

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

    partitions = remove_margin_from_partitions(partitions, top_margin);
    partitions.reverse();

    partitions = remove_margin_from_partitions(partitions, bottom_margin);
    partitions.reverse();

    // blow up the result to 100%;
    var total = sum_partitions(partitions);
    _.each(partitions, function(partition) {
        partition[0] = partition[0] / total * 100;
    });

    return partitions;
};

// renders the occupied partitions on an event
var render_partitions = function(event, element, calendar) {

    // if the event is being moved, don't render the partitions
    if (event.is_moving) {
        return;
    }

    var free = _.template('<div style="height:<%= height %>%;"></div>');
    var used = _.template('<div style="height:<%= height %>%;" class="calendar-occupied"></div>');
    var partition_block = _.template('<div style="height:<%= height %>px;"><%= partitions %></div>');

    // build the individual partitions
    var event_partitions = adjust_partitions(
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
    var html = partition_block({height: height, partitions: partitions});
    $('.fc-bg', element).wrapInner(html);
};

var event_after_render = function(event, element, view) {
    render_partitions(event, element, view.calendar);

    if (_.contains(view.calendar.options.highlights, event.id)) {
        $(element).addClass('highlight');
    }

    $(element).click(function() {
        spawn_popup(event, element);
    });
};

var setup_calendar = function(calendar) {
    var availableViews = calendar.data('available-views').split(',');
    var defaultView = calendar.data('default-view');
    var isPopping = false;
    var isFirst = true;

    if (!_.contains(availableViews, defaultView)) {
        defaultView = availableViews[0];
    }

    var onViewChange = function() {};

    if (window.history) {
        onViewChange = function(view) {
            if (isPopping) {
                return;
            }

            var url = new Url(window.location.href);
            url.query.view = view.name;
            url.query.date = view.intervalStart.format('YYYYMMDD');

            if (isFirst) {
                window.history.replaceState({
                    'view': view.name,
                    'date': view.intervalStart
                }, view.title, url.toString());
                isFirst = false;
            } else {
                window.history.pushState({
                    'view': view.name,
                    'date': view.intervalStart
                }, view.title, url.toString());
            }
        };

        window.onpopstate = function(event) {
            isPopping = true;
            calendar.fullCalendar('changeView', event.state.view);
            calendar.fullCalendar('gotoDate', event.state.date);
            isPopping = false;
        };
    }

    calendar.fullCalendar({
        events: calendar.data('feed'),
        header: {
            left: calendar.data('header-left'),
            center: calendar.data('header-center'),
            right: calendar.data('header-right')
        },
        allDaySlot: false,
        minTime: calendar.data('min-time'),
        maxTime: calendar.data('max-time'),
        selectable: calendar.data('selectable'),
        select: new_select_handler(calendar.data('select-url')),
        defaultView: defaultView,
        eventAfterRender: event_after_render,
        editable: calendar.data('editable'),
        eventDrop: edit_handler,
        eventResize: edit_handler,
        eventDragStart: function(event) {
            event.is_changing = true;
        },
        eventResizeStart: function(event) {
            event.is_changing = true;
        },
        viewRender: onViewChange,
        highlights: calendar.data('highlights')
    });

    if (calendar.data('goto-date')) {
        calendar.fullCalendar('gotoDate', calendar.data('goto-date'));
    }
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setup_calendar);
});
