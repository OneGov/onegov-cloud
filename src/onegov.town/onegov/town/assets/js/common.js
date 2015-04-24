// intercooler has the abilty to redirect depending on response headers
// we'd like for it to do the same with our own 'redirect-after' attribute
$('a').on('success.ic', function(evt, elt, data, textStatus, xhr) {
    var redirect_after = $(elt).attr('redirect-after');
    if (! _.isUndefined(redirect_after)) {
        window.location = redirect_after;
    }
});

// show the new content placeholder when hovering over the add content dropdown
$('#add-content').find('a')
    .on('mouseenter', function() {
        $('.new-content-placeholder').text($(this).text()).show();
    })
    .on('mouseleave', function() {
        $('.new-content-placeholder').hide();
    });

// initialize all foundation functions
$(document).foundation();
