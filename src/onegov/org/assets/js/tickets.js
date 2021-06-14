$('#edit-ticket-amount').on('click', function (e) {
    var edit = $(e.target);
    var netAmount = edit.prev('span');

    netAmount.hide();
    edit.hide();
    var checkIcon = fa_version === 5 ? 'far fw fa-check-circle': 'fa fw fa-check-circle-o'

    var field = $(`<input type="text" value="${netAmount.text()}">`);
    var submit = $(`<i id="confirm-ticket-amount" class="${checkIcon}"></i>`);
    submit.on('click', function () {
        var new_amount = field.val().trim().replace(/(\d+\.?\d?)\s(\w+)/, "$1");
        $.ajax({type: "POST", url: edit.parent().attr('data-edit') + `&netAmount=${new_amount}`})
            .done(function(data) {
                netAmount.text(data.net_amount);
                netAmount.toggleClass('flash');
            }).always(function () {
                submit.remove();
                field.remove();
                netAmount.show();
                edit.show();
        });
    });

    netAmount.after(field);
    field.after(submit);
    netAmount.hide();

});