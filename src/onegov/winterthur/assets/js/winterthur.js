// replace checkmarks in directory entries
$(document).ready(function() {
    $('.field-display dd').html(function() {
        return $(this).html().split('<br>').map(function(html) {
            return html.replace(/^\s*[✓\-]{1}/, ' •');
        }).join('<br>');
    });
});

// add hover clicks to directory entries
$(document).ready(function() {
    $('.directory-entry-collection-layout .with-lead li').click(function(e) {
        window.location = $(this).find('a').attr('href');
        e.preventDefault();
    });
});

// the search reset button in the directory search resets the whole view
$(document).ready(function() {
    $('#inline-search .reset-button').click(function(e) {
        var $form = $(this).closest('form');
        var $inputs = $form.find('input');

        $inputs.val('');
        $form.find('input[name="search"]').val('inline');
        $inputs.filter(':visible:first').removeAttr('required');

        $form.submit();

        e.preventDefault();
    });
});

// adjust all links that point to an external domain to target _top in order
// to escape the iframe we're in
$(document).ready(function() {
    var internal = new RegExp("^http[s]?://(forms.winterthur.ch|" + window.location.hostname + ").*", "i");

    $('a[href^="http"]').each(function() {
        var a = $(this);

        if (!a.attr('href').match(internal) && !a.is('[target]')) {
            a.attr('target', '_top');
        }
    });
});
