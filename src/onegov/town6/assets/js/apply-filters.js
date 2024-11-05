// Desktop: Apply filters when dropdown is closed
$('.filters-top .dropdown-pane').on('hide.zf.dropdown', function() {
    console.log('I did it')
    Intercooler.triggerRequest($(this).find('.apply-filters'))
})

// Mobile: Apply filters when dropdown is closed
$('.filters-mobile filter-panel').on('up.zf.accordionMenu', function() {
    Intercooler.triggerRequest($(this).find('.apply-filters'))
})