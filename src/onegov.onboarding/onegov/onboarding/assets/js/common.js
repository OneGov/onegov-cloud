$(document).ready(function() {

    /*
        Color picker prefilled with a set of colors well suited for onegov.
    */
    $('#color').colorPicker({
        pickerDefault: '005ba1',
        colors: [
            'a900f2',
            '9400d3',
            '7f00b4',
            '690096',
            '540077',
            '3e0059',
            '007ede',
            '006cc0',
            '005ba1',
            '004a82',
            '003864',
            '002745',
            '1f1fff',
            '0000ff',
            '0000e0',
            '0000c2',
            '0000a3',
            '000085',
            '009f00',
            '008000',
            '006100',
            '004300',
            '002400',
            '000600',
            'ff8f1f',
            'ff8000',
            'e07100',
            'c26100',
            'a35200',
            '854300',
            'ff1f1f',
            'ff0000',
            'e00000',
            'c20000',
            'a30000',
            '850000',
            '505050',
            '424242',
            '303030',
            '1f1f1f',
            '0f0f0f',
            '000000'
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
