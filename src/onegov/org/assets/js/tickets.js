$('#edit-ticket-email').on('click', function(e) {
    var edit = $(e.target);
    var email = edit.prev('a');
    var icon = email.prev('i');

    email.hide();
    icon.hide();
    edit.hide();
    var checkIcon = fa_version === 5 ? 'far fw fa-check-circle' : 'fa fw fa-check-circle-o';

    var field = $(`<input type="text" value="${email.text()}">`);
    field.css({
        fontSize: '.875rem !important',
        lineHeight: '1.2',
        width: 'calc(100% - 2em)',
        margin: '0 .5em .5em 0',
        display: 'inline-block'
    });
    var submit = $(`<i id="confirm-ticket-email" class="${checkIcon}"></i>`);
    submit.css({cursor: 'pointer'});
    submit.on('click', function() {
        var new_email = field.val().trim();
        $.ajax({
            type: "POST",
            url: edit.parent().attr('data-edit'),
            data: {email: new_email}
        }).done(function(data) {
            email.text(data.email);
            email.attr('href', `mailto:${data.email}`);
            email.toggleClass('flash');
        }).always(function() {
            submit.remove();
            field.remove();
            email.show();
            icon.show();
            edit.show();
        });
    });

    email.after(field);
    field.after(submit);
    email.hide();
    icon.hide();
}).css({cursor: 'pointer'});
