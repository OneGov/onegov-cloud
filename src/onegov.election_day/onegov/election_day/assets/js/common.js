// initialize all foundation functions
$(document).foundation();

// stack tables wishing to be stacked
$('.stackable').stacktable();

// collapse tables whising to be collapsible
$('.collapsible.collapsed tbody tr:not(.total):not(.sticky-row):not(.more)').hide();
$('.collapsible .more, .collapsible .less').click(function() {
    $(this).parents('table').toggleClass('collapsed');
    $(this).parents('table').children('tbody').children('tr:not(.total):not(.sticky-row)').toggle();
});

// sort tables wishing to be sorted
$('table.sortable').tablesorter({widgets: ['staticRow']});

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

// force all dropdowns to be rendered in the direction specified in the
// options of said dropdown (so if we say align:left, *always* align left)
Foundation.libs.dropdown.small = function() { return false; };
