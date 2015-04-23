// run at the end of the common js bundle
$(document).foundation();

// intercooler has the abilty to redirect depending on response headers
// we'd like for it to do the same with our own 'redirect-after' attribute
$('a').on('success.ic', function(evt, elt, data, textStatus, xhr) {
    var redirect_after = $(elt).attr('redirect-after');
    if (! _.isUndefined(redirect_after)) {
        window.location = redirect_after;
    }
});
