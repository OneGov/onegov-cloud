$('.print[data-print-selector]').click(function(e) {
    var el = $(this);
    $(el.data('print-selector')).printThis({
        'pageTitle': el.data('print-title') || '',
        'loadCSS': el.data('print-css') || ''
    });

    e.preventDefault();
});
