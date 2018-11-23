// Redirects to the selected option of a select
$('select.redirectable').on('change', function() {
    window.location.href = $(this).val();
});
