// initialize all foundation functions
$(document).foundation();

// Make the extended filters of the search collapsible
var initSearchFilters = function() {
    var fieldsetLegend = $('#fieldset-other-filters legend');
    var key = 'fieldset-other-filters-hidden';

    fieldsetLegend.click(function() {
        var fieldset = $(this).parent('fieldset');
        localStorage.setItem(key, fieldset.hasClass('collapsed') ? 'visible' : 'hidden');
        fieldset.toggleClass('collapsed').children('.formfields').toggle();
    });

    if (key in localStorage) {
        var value = localStorage.getItem(key);
        if (value == 'hidden') {
            fieldsetLegend.click();
        }
    } else {
        fieldsetLegend.click();
    }
};
initSearchFilters();

// Make the vote detail tables collapsible
$('table.collapsible thead').click(function() {
    $(this).parent('table').toggleClass('collapsed');
});

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
