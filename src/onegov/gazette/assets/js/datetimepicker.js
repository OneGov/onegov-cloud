// load the datetimepicker for date inputs if the browser does not support it
jQuery.datetimepicker.setLocale('de');

if (!Modernizr.inputtypes['date']) {
    $('input[type=date]').datetimepicker({
        allowBlank: true,
        dayOfWeekStart: 1, // Monday
        format: 'Y-m-d',   // HTML5 (RFC3339)
        lazyInit: true,
        timepicker: false
    });
}
if (!Modernizr.inputtypes['datetime-local']) {
    $('input[type=datetime-local]').datetimepicker({
        allowBlank: true,
        dayOfWeekStart: 1, // Monday
        format: 'Y-m-d H:i',   // HTML5
        // The correct format would be 'Y-m-d\\TH:i', but the code is too buggy
        lazyInit: true,
        timepicker: true
    });
}
