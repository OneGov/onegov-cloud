// check password strength
$('#password').on('input propertychange paste', function() {
    var password = $(this).val();
    var score = zxcvbn(password).score;
    if ($(this).next('meter').length) {
        $(this).next('meter').val(score);
    } else {
        $(this).after('<meter max="4" value="' + score + '"></meter>');
    }
});
