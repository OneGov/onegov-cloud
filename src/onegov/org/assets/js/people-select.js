var people_row_template = null;

function init_people_field(row) {
    row.find('.people-select').chosen({
        allow_single_deselect: true,
        search_contains: true,
        width: '100%'
    }).on('show', function() {
        $(this).hide();
    }).on('change', function() {
        var rows = $('div[id^="people-"]');
        var person_id = $(this).val();
        var person_fun = '';
        var fun_show = false;
        if (person_id) {
            var option = $(this).find('option[value="' + person_id + '"]');
            person_fun = option.data('function') || null;
            fun_show = option.data('show');
            if (fun_show === undefined) {
                fun_show = person_fun && true;
            }
        }
        var this_row = $(this).parent().parent().parent();
        var fun_field = this_row.find('input[name$="context_specific_function"]');
        var show_field = this_row.find('input[name$="in_person_directory"]');

        fun_field.val(person_fun);
        show_field.prop('checked', fun_show);

        // we need to add an additional line
        if (rows.last().find('.people-select').val()) {
            // eslint-disable-next-line no-use-before-define
            add_row();
        } else if (!person_id && !this_row.is(':last-child')) {
            // hide the choice, but don't delete it
            this_row.hide();
        }
    });
}

function add_row() {
    var rows = $('div[id^="people-"]');
    var row = people_row_template.clone();
    row.attr('id', 'people-' + rows.length);

    // also update the ids of all the contained elements
    var html = row.html();
    html = html.replace(/people-0/g, 'people-' + rows.length);
    row.html(html);

    rows.first().parent().append('<br>', row);

    setup_depends_on(row);
    init_people_field(row);
}

$(document).ready(function() {
    var rows = $('div[id^="people-"]');
    people_row_template = rows.first().clone();
    // make the template blank
    people_row_template.find('option:selected').removeAttr('selected');
    people_row_template.find('input:checked').removeAttr('checked');
    people_row_template.find('input[type=text]').attr('value', '');
    init_people_field(rows);
});
