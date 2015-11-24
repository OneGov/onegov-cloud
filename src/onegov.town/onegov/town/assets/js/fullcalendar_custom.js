var new_select_handler = function(url) {
    return function(start, end, jsEvent, view) {
        var params = '';

        if (view.name == "month") {
            params = '?start=' + start.toISOString() + '&end=' + end.subtract(1, 'days').toISOString() + '&whole_day=yes';
        } else {
            params = '?start=' + start.toISOString() + '&end=' + end.toISOString() + '&whole_day=no';
        }
        location.href = url.split('?')[0] + params;
    };
};

var edit_handler = function(event, delta, revertFunc, jsEvent, ui, view) {
    location.href = event.editurl + '?start=' + event.start.toISOString() + '&end=' + event.end.toISOString();
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

    function round(num) {
        return +(Math.round(num + "e+2")  + "e-2");
    }

    function sum(partitions) {
        return _.reduce(partitions, function(total, p) {
            return total + p[0];
        }, 0);
    }

    // the event is rendered within the calendar, with the top and
    // bottom cut off. The partitions are calculated assuming the
    // event is being rendered as a whole. To adjust we cut the
    // bottom and top from the partitions and blow up the whole event.
    //
    // It made sense when I wrote the initial implementation :)
    var percentage_per_hour = 1/duration*100;
    var top_margin = 0, bottom_margin = 0;

    if (start_hour < min_hour) {
        top_margin = (min_hour - start_hour) * percentage_per_hour;
    }
    if (end_hour > max_hour) {
        bottom_margin = (end_hour - max_hour) * percentage_per_hour;
    }

    // remove the given margin from the top of the partitions array
    // the margin is given as a percentage
    var remove_margin = function(partitions, margin) {

        if (margin === 0) {
            return partitions;
        }

        var removed_total = 0;
        var original_margin = margin;

        for (var i=0; i < partitions.length; i++) {
            if (round(partitions[i][0]) >= round(margin)) {
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

    partitions = remove_margin(partitions, top_margin);
    partitions.reverse();

    partitions = remove_margin(partitions, bottom_margin);
    partitions.reverse();

    // blow up the result to 100%;
    var total = sum(partitions);
    _.each(partitions, function(partition, index) {
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
    var html = partition_block({height:height, partitions:partitions});
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
        defaultView: calendar.data('default-view'),
        eventAfterRender: event_after_render,
        editable: calendar.data('editable'),
        eventDrop: edit_handler,
        eventResize: edit_handler,
        eventDragStart: function(event, jsEvent, ui, view ) {
            event.is_changing = true;
        },
        eventResizeStart: function( event, jsEvent, ui, view ) {
            event.is_changing = true;
        },
        highlights: calendar.data('highlights')
    });

    if (calendar.data('goto-date')) {
        calendar.fullCalendar('gotoDate', calendar.data('goto-date'));
    }
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setup_calendar);
});
