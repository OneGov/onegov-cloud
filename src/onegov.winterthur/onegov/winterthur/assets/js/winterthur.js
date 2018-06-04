$(document).ready(function() {
    $('.field-display dd').text(function() {
        return $(this).text().replace('✓', '•');
    });
});