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

// fold sections whising to be foldable
$('.foldable.folded .foldable-panel').hide();
$('.foldable .foldable-title').click(function() {
    $(this).parents('.foldable').toggleClass('folded');
    $(this).parents('.foldable').find('.foldable-panel').toggle();
});

// force all dropdowns to be rendered in the direction specified in the
// options of said dropdown (so if we say align:left, *always* align left)
Foundation.libs.dropdown.small = function() { return false; };
