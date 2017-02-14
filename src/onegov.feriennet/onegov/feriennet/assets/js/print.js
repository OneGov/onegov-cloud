$('.print[data-print-selector]').click(function(e) {
    var el = $(this);

    if ($(el).data('is-print-hooked') !== true) {
        $(el.data('print-selector')).printThis({
            'pageTitle': el.data('print-title') || '',
            'loadCSS': el.data('print-css') || ''
        });
        $(el).data('is-print-hooked', true);
    }

    e.preventDefault();
});
