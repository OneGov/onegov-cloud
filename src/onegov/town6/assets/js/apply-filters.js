// Apply filters when dropdown is closed
$('.filter-panel').on('hide.zf.dropdown', function() {
    Intercooler.triggerRequest($(this).find('.apply-filters'))
})