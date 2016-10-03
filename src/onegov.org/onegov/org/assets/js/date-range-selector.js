// set date filter on input change
var set_date_range_selector_filter = function(name, value) {
    var location = new Url();
    location.query[name] = convert_date(value, datetimepicker_i18n[get_locale()].dateformat_momentjs, 'Y-m-d');
    delete location.query.page;
    window.location.href = location.toString();
};

if (Modernizr.inputtypes.date) {
    $('.date-range-selector input[type="date"]').on('input', function() {
        set_date_range_selector_filter($(this).attr('name'), $(this).val());
    });
} else {
    $('.date-range-selector input[type="date"]').each(function() {
        $(this).datetimepicker({
            onChangeDateTime: function(_dp, $input) {
                set_date_range_selector_filter($input.attr('name'), $input.val());
            }
        });
    });
}
