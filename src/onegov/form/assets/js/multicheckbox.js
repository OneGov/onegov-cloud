$(document).ready(function() {
    $('ul').each(function(_, element) {
        var checkboxes = $(element).children('li').children('input[type="checkbox"]');
        if (checkboxes.length < 5) {
            return;
        }
        var name = checkboxes.eq(0).attr('name');
        if (!name) {
            return;
        }
        for (var i = 1; i < checkboxes.length; i++) {
            if (checkboxes.eq(i).attr('name') !== name) {
                // not a real multi checkbox field
                return;
            }
        }

        var select_label = {
            de: 'Alles auswählen',
            en: 'Select all',
            fr: 'Sélectionner tout',
            it: 'Seleziona tutto'
        };
        var deselect_label = {
            de: 'Alles abwählen',
            en: 'Deselect all',
            fr: 'Désélectionner tout',
            it: 'Deseleziona tutto'
        };
        var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";
        var select_button = $('<label>' + select_label[language] + '</label>');
        var deselect_button = $('<label>' + deselect_label[language] + '</label>');
        var divider = $('<label>|</label>').css({margin: '0 .25rem'});
        $([select_button[0], deselect_button[0]]).css({cursor: 'pointer'});
        select_button.on('click', function() {
            checkboxes.not(':checked').trigger('click');
        });
        deselect_button.on('click', function() {
            checkboxes.filter(':checked').trigger('click');
        });
        $(element).prepend($('<li></li>').append(select_button).append(divider).append(deselect_button));
    });
});
