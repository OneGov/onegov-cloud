// initialize all foundation functions
$(document).foundation();

// stack tables wishing to be stacked
$('.stackable').stacktable();

// dropdowns wishing to be chosened
$('.chosen-select').chosen({
    no_results_text: "Keine Ergebnisse gefunden:",
    placeholder_text_multiple: "Mehrere Optionen auswählen",
    placeholder_text_single: "Eine Option auswählen",
    search_contains: true
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

// force all dropdowns to be rendered in the direction specified in the
// options of said dropdown (so if we say align:left, *always* align left)
Foundation.libs.dropdown.small = function() { return false; };

// Hide the first x options in a limited multi select form field
$('ul[data-limit]').each(function() {
    var ul = $(this);
    ul.children('li:not(.expand)').slice(ul.data('limit')).hide();
    ul.append(
        $('<li></li>')
            .attr('class', 'expand')
            .html(
                $('<a></a>')
                .attr('href', '#')
                .attr('class', 'action-expand')
                .on('click', function() {
                    ul.children('li:not(.expand)').show();
                    ul.children('li.expand').hide();
                    return false;
                })
                .html(ul.data('expand-title') || 'Show all')
            )
    );
    ul.append(
        $('<li></li>')
            .attr('class', 'fold')
            .html(
                $('<a></a>')
                .attr('href', '#')
                .attr('class', 'action-fold')
                .on('click', function() {
                    ul.children('li:not(.expand)').slice(ul.data('limit')).hide();
                    ul.children('li.expand').show();
                    ul.children('li.fold').hide();
                    return false;
                })
                .html(ul.data('fold-title') || 'Show less')
            )
            .hide()
    );
});

// Highlight the hot issue
$('ul[data-hot-issue]').each(function() {
    var issue = $(this).data('hot-issue');
    var input = $("input[value='" + issue + "']").attr('id');
    $("label[for='" + input + "']").addClass('warning');
});
