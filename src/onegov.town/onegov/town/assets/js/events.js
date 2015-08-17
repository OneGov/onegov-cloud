// set date filter on input change
var set_date_filter = function(name, value) {
    var location = new Url();
    location.query[name] = value;
    delete location.query.page;
    window.location.href = location.toString();
};

if (Modernizr.inputtypes.date) {
    $('input[type="date"]').on('input', function() {
        set_date_filter($(this).attr('name'), $(this).val());
    });
} else {
    $('input[type="date"]').each(function() {
        $(this).datetimepicker({
            onChangeDateTime: function(dp, $input) {
                set_date_filter($input.attr('name'), $input.val());
            }
        });
    });
}
