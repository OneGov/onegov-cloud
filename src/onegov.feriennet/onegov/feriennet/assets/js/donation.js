$(document).ready(function() {
    $('.donation-layout form .button').on('mouseenter', function() {
        $('#Eyes').attr('display', 'none');
        $('#Pleased').removeAttr('display');
    });

    $('.donation-layout form .button').on('mouseout', function() {
        $('#Pleased').attr('display', 'none');
        $('#Eyes').removeAttr('display');
    });
});
