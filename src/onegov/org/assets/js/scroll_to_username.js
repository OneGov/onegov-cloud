// Scroll to the input username field
$(document).ready(function () {
    var target = $('input#username')[0] || $('input#email')[0]
    if (target) {
        $('html, body').animate({
            scrollTop: target.offset().top
        }, 'slow');
    }
});
