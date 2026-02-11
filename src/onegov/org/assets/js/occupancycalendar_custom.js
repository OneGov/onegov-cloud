var setupOccupancyCalendar = function(calendar) {
    calendar.occupancyCalendar({
        feed: calendar.data('feed'),
        type: calendar.data('type'),
        minTime: calendar.data('min-time'),
        maxTime: calendar.data('min-time'),
        editable: calendar.data('editable'),
        view: calendar.data('view'),
        date: calendar.data('date'),
        highlights_min: calendar.data('highlights-min'),
        highlights_max: calendar.data('highlights-max'),
        stats_url: calendar.data('stats-url'),
        pdf_url: calendar.data('pdf-url'),
        resourcesUrl: calendar.data('resources-url'),
        resourceActive: calendar.data('resource-active')
    });
};

$(document).ready(function() {
    _.each(_.map($('.occupancy-calendar'), $), setupOccupancyCalendar);
});
