$(document).ready(function() {

    /*
        Color picker prefilled with a set of colors well suited for onegov.
    */
    $('#color').colorPicker({
        pickerDefault: '005ba1',
        colors: [
            '005ba1',
            '008e53',
            'd93c3d',
            'aa5790',
            '8590a1',
        ]
    });

    /*
        Autocomplete
    */
    $('input.autocomplete').each(function() {
        var input = $(this);
        var src = input.data('source');
        var url = $('body').data('source-' + src);

        $.ajax({type: "GET", url: url})
            .done(function(data) {
                new Awesomplete(input[0], {list: data, maxItems: 5});
            });
    });

    /*
        Prevent double clicks on submit forms
    */
    var prevent_double_click = function() {
        this.disabled = true;
        this.form.submit();
    };
    $('input[type="submit"]').each(function() {
        $(this).click(prevent_double_click);
    });

});
