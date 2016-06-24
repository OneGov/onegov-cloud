// initialize all foundation functions
$(document).foundation();

// stack tables wishing to be stacked
$('.stackable').stacktable();

// collapse tables whising to be collapsible
$('.collapsible.collapsed tbody tr:not(.total):not(.sticky):not(.more)').hide();
$('.collapsible .more, .collapsible .less').click(function() {
    $(this).parents('table').toggleClass('collapsed');
    $(this).parents('table').children('tbody').children('tr:not(.total):not(.sticky)').toggle();
});

// fold sections wishing to be foldable
$('.foldable.folded .foldable-panel').hide();
$('.foldable .foldable-title').click(function() {
    $(this).parents('.foldable').toggleClass('folded');
    var hide = $(this).parents('.foldable').hasClass('folded');
    if (hide) {
        $(this).parents('.foldable').find('.foldable-panel').hide();
        $(this).parents('.foldable').find('.foldable-svg-panel').hide();
    } else {
        $(this).parents('.foldable').find('.foldable-panel').show();
        $(this).parents('.foldable').find('.foldable-svg-panel').show();
    }
});

// force all dropdowns to be rendered in the direction specified in the
// options of said dropdown (so if we say align:left, *always* align left)
Foundation.libs.dropdown.small = function() { return false; };
