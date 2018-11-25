// initialize all foundation functions
$(document).foundation();

// stack tables wishing to be stacked
$('.stackable').stacktable();

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

// Set up the chosen select in the subnavs (they have a different width)
$('.sub-nav-chosen-select').chosen({
    search_contains: true,
});

// Submit the whole notice selection/form when clicking on the state links,
// the chosen selects or the checkbox.
$('a.notice-filter').click(function(event) {
    var form = $(this).parents('form');
    form.attr('action', this.getAttribute('href'));
    form.submit();
    event.preventDefault();
});
$('input[name=own]').on('change', function() {
    $(this).parents('form').submit();
});
$('.sub-nav-chosen-select').on('change', function() {
    $(this).parents('form').submit();
});

// Fill the notice filter dates when clicking on the date shortcuts
$('.date-shortcut').click(function() {
    var date = $(this).data('date');
    $('input[name=from_date]').val(date);
    $('input[name=to_date]').val(date);
});
$('.sub-nav.issue select').on('change', function() {
    var date = $(this).val();
    $('input[name=from_date]').val(date);
    $('input[name=to_date]').val(date);
    $(this).parents('form').submit();
});

// Make the extended filters ncollapsible
var initSearchFilters = function() {
    var fieldsetLegend = $('fieldset#additional-filters legend');
    var key = 'fieldset-additional-filters-hidden';

    fieldsetLegend.click(function() {
        var fieldset = $(this).parent('fieldset');
        localStorage.setItem(key, fieldset.hasClass('collapsed') ? 'visible' : 'hidden');
        fieldset.toggleClass('collapsed').children('dl').toggle();
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
