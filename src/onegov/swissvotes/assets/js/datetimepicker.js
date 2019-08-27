// load the datetimepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes['date']) {
    $('input[type=date]').datetimepicker({
        allowBlank: true,
        dayOfWeekStart: 1, // Monday
        format: 'Y-m-d',   // HTML5 (RFC3339)
        lazyInit: true,
        timepicker: false
    });
}
