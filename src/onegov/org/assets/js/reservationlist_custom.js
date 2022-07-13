var setupReservationList = function(list) {
    list.reservationList({
        reservations: list.data('reservations'),
        reservationform: list.data('reservationform'),
        wholeDay: list.data('whole-day')
    });
};

$(document).ready(function() {
    _.each(_.map($('.reservation-list'), $), setupReservationList);
});
