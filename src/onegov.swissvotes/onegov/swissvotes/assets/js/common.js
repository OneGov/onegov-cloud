// initialize all foundation functions
$(document).foundation();

// Make the extended filters of the search collapsible
var initSearchFilters = function() {
    var fieldset = $('#fieldset-other-filters');
    var key = 'fieldset-other-filters-hidden';

    fieldset.click(function() {
        localStorage.setItem(key, $(this).hasClass('collapsed') ? 'visible' : 'hidden');
        $(this).toggleClass('collapsed').children('.formfields').toggle();
    });

    if (key in localStorage) {
        var value = localStorage.getItem(key);
        console.log('get ' + value);
        if (value == 'hidden') {
            console.log('clicking');
            fieldset.click();
        }
    } else {
        fieldset.click();
    }
};
initSearchFilters();


// Add backend dropdown actions
$('ul.actions').each(function(index, element) {
    $(element).before(
        $('<a></a>')
            .attr('href', '#')
            .attr('class', 'button split small action-button secondary')
            .on('click', function() { $(element).toggle(); return false; })
            .html($(this).data('title') + ' <span></span>')
    ).hide();
    $(element).parent('td').addClass('row-actions');
});

// sort tables wishing to be sorted (when not using tablesaw)
$('table:not(.tablesaw).sortable').tablesorter();

// force all dropdowns to be rendered in the direction specified in the
// options of said dropdown (so if we say align:left, *always* align left)
Foundation.libs.dropdown.small = function() { return false; };
