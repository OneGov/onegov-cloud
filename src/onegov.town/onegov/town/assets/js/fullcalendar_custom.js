var setup_calendar = function(calendar) {
    calendar.fullCalendar({});
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setup_calendar);
});
