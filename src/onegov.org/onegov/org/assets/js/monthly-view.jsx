var WEEKDAYS_SHORT = {
    de: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'],
    fr: ['Di', 'Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa']
};

var MONTHS = {
    de: [
        'Januar',
        'Februar',
        'März',
        'April',
        'Mai',
        'Juni',
        'Juli',
        'August',
        'September',
        'Oktober',
        'November',
        'Dezember'
    ],
    fr: [
        'Janvier',
        'Février',
        'Mars',
        'Avril',
        'Mai',
        'Juin',
        'Juillet',
        'Août',
        'Septembre',
        'Octobre',
        'Novembre',
        'Décembre'
    ]
};

var WEEKDAYS_LONG = {
    de: [
        'Sonntag',
        'Montag',
        'Dienstag',
        'Mittwoch',
        'Donnerstag',
        'Freitag',
        'Samstag'
    ],
    fr: [
        'Dimanche',
        'Lundi',
        'Mardi',
        'Mercredi',
        'Jeudi',
        'Vendredi',
        'Samedi'
    ]
};

var FIRST_DAY_OF_WEEK = {
    de: 1,
    fr: 1
};

var BUTTON_LABELS = {
    de: {
        nextMonth: 'nächster Monat',
        previousMonth: 'vorheriger Monat'
    },
    fr: {
        nextMonth: 'mois précédent',
        previousMonth: 'mois prochain'
    }
};

var MonthlyView = React.createClass({
    render: function() {
        var locale = $('html').attr('lang').substring(0, 2);

        return (
            <DayPicker
                locale={locale}
                months={MONTHS[locale]}
                weekdaysLong={WEEKDAYS_LONG[locale]}
                weekdaysShort={WEEKDAYS_SHORT[locale]}
                firstDayOfWeek={FIRST_DAY_OF_WEEK[locale]}
                labels={BUTTON_LABELS[locale]}
                selectedDays={this.props.selectedDays}
                fromMonth={this.props.selectedDays[0]}
                toMonth={this.props.selectedDays[this.props.selectedDays.length - 1]}
            />
        );
    }
});

var parseIsoDate = function(text) {
    var parts = text.split("-");

    return new Date(
        parseInt(parts[0], 10),
        parseInt(parts[1], 10) - 1,
        parseInt(parts[2], 10)
    );
};

var parseIsoDates = function(text) {
    var dates = (text || '').split(';');

    for (var i = 0; i < dates.length; i++) {
        dates[i] = parseIsoDate(dates[i]);
    }

    return dates;
};

jQuery.fn.monthlyView = function() {
    return this.each(function() {
        var target = $(this);

        var el = $('<div class="monthly-view-wrapper" />');
        el.appendTo(target);

        ReactDOM.render(
            <MonthlyView selectedDays={parseIsoDates(target.attr('data-dates'))} />,
            el.get(0)
        );
    });
};

$(document).ready(function() {
    $('.monthly-view').monthlyView();
});
