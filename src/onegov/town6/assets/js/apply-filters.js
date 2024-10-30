// Apply filters when dropdown is closed
$('.filter-pane').on('hide.zf.dropdown', function() {
    Intercooler.triggerRequest($(this).find('.apply-filters'))
})