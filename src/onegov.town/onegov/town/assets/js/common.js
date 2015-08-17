// intercooler has the abilty to redirect depending on response headers
// we'd like for it to do the same with our own 'redirect-after' attribute
$('a').on('success.ic', function(evt, elt, data, textStatus, xhr) {
    var redirect_after = $(elt).attr('redirect-after');
    if (! _.isUndefined(redirect_after)) {
        window.location = redirect_after;
    }

    return true;
});

// show the new content placeholder when hovering over the add content dropdown
$('.show-new-content-placeholder')
    .on('mouseenter', function() {
        $('.new-content-placeholder').text($(this).text()).show();
    })
    .on('mouseleave', function() {
        $('.new-content-placeholder').hide();
    });

// initialize all foundation functions
$(document).foundation();

// get the footer height and write it to the footer_height setting if possible
$(document).find('#footer_height').val($('footer > div').height() + 'px');

// load the datetimepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes.date) {
    $('input[type=date]').datetimepicker({
        allowBlank: true,
        dayOfWeekStart: 1, // Monday
        format: 'Y-m-d',   // HTML5 (RFC3339)
        lang: 'de',
        lazyInit: false,
        timepicker: false,
    });
}
