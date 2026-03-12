var kaba_row_template = null;

function init_kaba_field(row) {
    row.find('input[type="text"]').first().on('change', function() {
        var rows = $('div[id^="kaba_configurations-"]');
        var site_id = $(this).val();
        // we need to add an additional line
        if (rows.last().find('input[type="text"]').first().val()) {
            var new_row = kaba_row_template.clone();
            new_row.attr('id', 'kaba_configurations-' + rows.length);

            // also update the ids of all the contained elements
            new_row.html(new_row.html().replace(
                /kaba_configurations-0/g,
                'kaba_configurations-' + rows.length
            ));

            rows.first().parent().append(
                '<label><b>' + (rows.length + 1) + '.</b><label>',
                new_row
            );

            setup_depends_on(new_row);
            init_kaba_field(new_row);
        } else if (!site_id && !this_row.is(':last-child')) {
            // hide the choice, but don't delete it
            this_row.hide();
        }
    }).trigger('change');
}

$(document).ready(function() {
    var rows = $('div[id^="kaba_configurations-"]');
    kaba_row_template = rows.first().clone();
    // make the template blank
    kaba_row_template.find('option:selected').removeAttr('selected');
    kaba_row_template.find('input:checked').removeAttr('checked');
    kaba_row_template.find('input[type=text]').attr('value', '');
    rows.each(function(_i, row) { init_kaba_field($(row)); });
});
