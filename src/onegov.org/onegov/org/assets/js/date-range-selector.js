// set date filter on input change
var set_date_range_selector_filter = function(name, value) {
    var location = new Url();

    if (value === "") {
        delete location.query[name];
    } else {
        var date = moment(value, 'YYYY-MM-DD', true);
        if (!date.isValid()) {
            return;
        }

        var year = date.year();
        if (!(1900 <= year && year <= 2100)) {
            return;
        }

        location.query[name] = value;
    }

    delete location.query.page;
    delete location.query.range;

    var url = location.toString();
    var target = $('.date-range-selector-target');

    if (target.length === 0) {
        window.location.href = url;
    } else {
        $.get(url, function(data) {
            target.replaceWith($(data).find('.date-range-selector-target'));
            history.replaceState({}, "", url);
        });
    }
};

if (Modernizr.inputtypes.date) {
    $('.date-range-selector input[type="date"]').on('input', _.debounce(function() {
        set_date_range_selector_filter($(this).attr('name'), $(this).val());
    }, 300));
} else {
    $('.date-range-selector input[type="date"]').each(function() {
        $(this).datetimepicker({
            onChangeDateTime: function(_dp, $input) {
                set_date_range_selector_filter($input.attr('name'), convert_date($input.val(), datetimepicker_i18n[get_locale()].dateformat_momentjs, 'Y-m-d'));
            }
        });
    });
}
