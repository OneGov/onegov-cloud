// initialize all foundation functions
$(document).foundation();

// stack tables wishing to be stacked
$('.stackable').stacktable();

// dropdowns wishing to be chosened
$('.chosen-select').chosen();

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

// Hide the first x options in a limited multi select form field
$('ul[data-limit]').each(function() {
    $(this).children('li:not(.expand)').slice($(this).data('limit')).hide();
    $(this).append(
        $('<li></li>')
            .attr('class', 'expand')
            .html(
                $('<a></a>')
                .attr('href', '#')
                .attr('class', 'action-expand')
                .on('click', function() {
                    $(this).closest('ul').children('li:not(.expand)').show();
                    $(this).hide();
                    return false;
                })
                .html($(this).data('expand-title') || 'Show all')
            )
    );
});
