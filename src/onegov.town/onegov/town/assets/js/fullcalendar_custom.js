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
        defaultView: calendar.data('default-view')
    });
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setup_calendar);
});
