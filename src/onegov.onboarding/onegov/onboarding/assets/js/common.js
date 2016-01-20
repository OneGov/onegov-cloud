$(document).ready(function() {

    /*
        Color picker with predefined values
    */
    $('#color').colorPicker({
        pickerDefault: '005BA1',
        colors: [
            'B30000',
            '886600',
            '2A7400',
            '1E5453',
            '2A6275',
            '005BA1',
            '4A58C4',
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
});
