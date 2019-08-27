var setupReservationCalendar = function(calendar) {
    calendar.reservationCalendar({
        feed: calendar.data('feed'),
        type: calendar.data('type'),
        minTime: calendar.data('min-time'),
        maxTime: calendar.data('min-time'),
        editable: calendar.data('editable'),
        selectUrl: calendar.data('select-url'),
        editUrl: calendar.data('edit-url'),
        view: calendar.data('view'),
        date: calendar.data('date'),
        highlights_min: calendar.data('highlights-min'),
        highlights_max: calendar.data('highlights-max'),
        reservations: calendar.data('reservations'),
        reservationform: calendar.data('reservationform'),
        resourcesUrl: calendar.data('resources-url'),
        resourceActive: calendar.data('resource-active')
    });
};

$(document).ready(function() {
    _.each(_.map($('.calendar'), $), setupReservationCalendar);
});
