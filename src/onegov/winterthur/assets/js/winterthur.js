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


$(document).ready(function() {
    const fieldsWithOnlyPositiveNumbers = ['#duration', '#personnel', '#backup', "#mission_count"];
    const regexp = /^vehicles_.*_count$/;
    const vehicleCountField = [...document.querySelectorAll("[id]")].filter(el => regexp.test(el.id));
    const nonNullinputFields = fieldsWithOnlyPositiveNumbers.map(numberFields =>
        document.querySelector(numberFields)).concat(vehicleCountField).filter(field => field !== null
    );
    validateOnPositiveIntegers(nonNullinputFields);
});

// Allow numbers, backspace, delete, left and right arrow keys to be entered in fields.
// Prevent everything else.
function validateOnPositiveIntegers(integerFields) {

    function validateKeyCode(event) {
        const code = event.keyCode;
        if (code === 8 || code === 46 || code === 37 || code === 39) {
            return true;
        } else if (code < 48 || code > 57) {
            return false;
        } else return true;
    }

    integerFields.forEach(field => {
        field.addEventListener('keypress', function (event) {
            if (!validateKeyCode(event)) {
                event.preventDefault();
            }
        });
    });
}
