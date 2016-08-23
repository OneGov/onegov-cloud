// check password strength
var check_password_strength = function() {
    var password = $(this).val();
    var score = zxcvbn(password).score;

    if ($(this).next('meter').length) {
        $(this).next('meter').val(score);
    } else {
        $(this).after('<meter max="4" value="' + score + '"></meter>');
    }
};
$('#password').on('input propertychange paste', check_password_strength);
$(document).ready(function (){
    check_password_strength.apply($('#password'));
});