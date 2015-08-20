var new_select_handler = function(url) {
    return function(start, end, jsEvent, view) {
        var params = '';

        if (view.name == "month") {
            params = '?start=' + start.toISOString() + '&end=' + end.subtract(1, 'days').toISOString() + '&whole_day=yes';
        } else {
            params = '?start=' + start.toISOString() + '&end=' + end.toISOString() + '&whole_day=no';
        }
        location.href = url + params;
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
        'transition': 'all 0.3s',
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

var event_after_render = function(event, element, view) {
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
        eventResize: edit_handler
    });

    if (calendar.data('goto-date')) {
        calendar.fullCalendar('gotoDate', calendar.data('goto-date'));
    }
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setup_calendar);
});
