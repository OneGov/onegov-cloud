var setup_calendar = function(calendar) {
    calendar.fullCalendar({
        events: calendar.data('feed')
    });
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setup_calendar);
});
