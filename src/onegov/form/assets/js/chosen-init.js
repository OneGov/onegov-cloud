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
                if (value !== null) {
                    $('#' + id).find(
                        'input[value="' + String(value).replace(/"/g, '\\"') + '"]'
                    ).not(':checked').trigger('click');
                }
            });
        }
    });

    var label = {
        de: 'Formular zurücksetzen',
        en: 'Reset form',
        fr: 'Réinitialiser le formulaire',
        it: 'Modulo di reset'
    };
    var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

    $('form.resettable').each(function(_, element) {
        var button = $('<a href="#" class="button">' + label[language] + '</a>');
        $(element).prepend(button);
        button.click(function() {
            $(element).find('input[type="checkbox"]:checked').trigger('click');
            // eslint-disable-next-line max-nested-callbacks
            $(element).find('.field-type-radiofield').each(function(_i, field) {
                $(field).find('input[type="radio"]').eq(0).trigger('click');
            });
            $(element).find(
                'input[type="radio"]:checked'
            ).prop('checked', false).trigger('change');
            $(element).find('select').val('').filter('.chosen-select').trigger('chosen:updated');
            $(element).find('input').not(
                '[type="submit"], [type="radio"], [type="checkbox"], [name="csrf_token"]'
            ).val('').trigger('change');
            return false;
        });
    });
});
