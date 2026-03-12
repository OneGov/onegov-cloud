var participant_row_template = null;

function init_participant_field(row) {
    row.find('.participant-select').chosen({
        allow_single_deselect: true,
        search_contains: true,
        width: '100%'
    }).on('show', function() {
        $(this).hide();
    }).on('change', function() {
        var rows = $('div[id^="participants-"]');
        var participant_id = $(this).val();
        var role = '';
        if (participant_id) {
            var option = $(this).find('option[value="' + participant_id + '"]');
            role = option.data('role') || null;
        }
        var this_row = $(this).parent().parent().parent();
        var role_field = this_row.find('select[name$="participant_type"]');

        role_field.val(role);

        // we need to add an additional line
        if (rows.last().find('.participant-select').val()) {
            var new_row = participant_row_template.clone();
            new_row.attr('id', 'participants-' + rows.length);

            // also update the ids of all the contained elements
            var html = new_row.html();
            html = html.replace(/participants-0/g, 'participants-' + rows.length);
            new_row.html(html);

            rows.first().parent().append('<br>', new_row);

            setup_depends_on(new_row);
            init_participant_field(new_row);
        } else if (!participant_id && !this_row.is(':last-child')) {
            // hide the choice, but don't delete it
            this_row.hide();
        }
    });
}

$(document).ready(function() {
    var rows = $('div[id^="participants-"]');
    participant_row_template = rows.first().clone();
    // make the template blank
    participant_row_template.find('option:selected').removeAttr('selected');
    participant_row_template.find('input:checked').removeAttr('checked');
    participant_row_template.find('input[type=text]').attr('value', '');
    init_participant_field(rows);
});
