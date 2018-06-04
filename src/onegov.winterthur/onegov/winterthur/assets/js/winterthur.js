$(document).ready(function() {
    $('.field-display dd').html(function() {
        return $(this).html().split('<br>').map(function(html) {
            return html.replace(/\s*[✓\-]{1}/, ' •');
        }).join('<br>');
    });
});