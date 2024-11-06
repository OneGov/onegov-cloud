// Desktop: Apply filters when dropdown is closed
$('#filters-top .dropdown-pane').on('hide.zf.dropdown', function() {
    console.log('hide')
    Intercooler.triggerRequest($(this).find('.apply-filters'))
})

// Mobile: Apply filters when dropdown is closed
$('#offCanvasFilters').on('close.zf.offCanvas', function() {
    Intercooler.triggerRequest($(this).find('.apply-filters'))
})

$( document ).ready(function() {
    const config = { attributes: true };

    const topFilters = document.getElementById('content');
    const callbackTF = function(mutationsList, observer) {
        for (const mutation of mutationsList) {
            $('#filters-top').foundation();
        }
    };
    
    if (topFilters) {
        const topFilterObserver = new MutationObserver(callbackTF);
        topFilterObserver.observe(topFilters, config);
    }
    
    const mobileFilters = document.getElementById('offCanvasFilters');
    const callbackMF = function(mutationsList, observer) {
        for (const mutation of mutationsList) {
            $('#offCanvasFilters').foundation();
        }
    };

    
    if (mobileFilters) {
        const mobileFilterObserver = new MutationObserver(callbackMF);
        mobileFilterObserver.observe(mobileFilters, config);

       $(window).on('beforeAjaxSend.ic', function(event, settings, element) {
            const url = new URL(settings.url)
            const filter = $('#offCanvasFilters .accordion .is-active ul').attr('id')
            url.searchParams.set('active-filter', filter)
            settings.url = url.toString()
        });
    }
});