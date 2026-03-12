// Desktop: Apply filters when dropdown is closed
$('body').on('hide.zf.dropdown', function(event) {
    const target = event.target;
    const filtersTop = document.getElementById('filters-top');

    if (filtersTop && filtersTop.contains(
        target) && target.matches('.dropdown-pane')) {
        Intercooler.triggerRequest($(target).find('.apply-filters'));
    }
});

// Mobile: Apply filters when dropdown is closed
$('#offCanvasFilters').on('close.zf.offCanvas', function() {
    Intercooler.triggerRequest($(this).find('.apply-filters'));
});

$(function () {
    const config = { attributes: true };

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