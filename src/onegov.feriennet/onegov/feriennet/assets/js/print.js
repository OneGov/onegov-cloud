$('.print[data-print-selector]').click(function() {
    var el = $(this);

    $(el.data('print-selector')).printThis({
        'pageTitle': el.data('print-title') || ''
    });
});
