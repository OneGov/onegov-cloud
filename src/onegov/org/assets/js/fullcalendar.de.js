
$.fullCalendar.locale("de", {
    buttonText: {
        month: "Monat",
        week: "Woche",
        day: "Tag",
        list: "Terminübersicht",
        today: "Heute"
    },
    allDayText: "Ganztägig",
    eventLimitText: function(n) {
        return "+ weitere " + n;
    }
});
