$(document).ready(function() {
    $('.chosen-select').chosen({
        search_contains: true,
        allow_single_deselect: true,
        width: '100%'
    }).on('show', function() {
        $(this).hide();
    }).filter('[data-auto-fill]').on('change', function() {
        var field = $(this);
        var data = field.data('auto-fill')[field.val()];
        if (data !== undefined) {
            $.each(data, function(id, value) {
                $('#' + id).val(value).trigger('change');
            });
        }
    });
});
