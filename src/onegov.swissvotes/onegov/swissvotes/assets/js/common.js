// initialize all foundation functions
$(document).foundation();

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

// dropdowns wishing to be chosened
$('.chosen-select').chosen({
    no_results_text: "Keine Ergebnisse gefunden:",
    placeholder_text_multiple: "Mehrere Optionen auswählen",
    placeholder_text_single: "Eine Option auswählen",
    search_contains: true,
    width: '100%'
});


// force all dropdowns to be rendered in the direction specified in the
// options of said dropdown (so if we say align:left, *always* align left)
Foundation.libs.dropdown.small = function() { return false; };
