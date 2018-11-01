// Redirects to the selected option of a select
$('select.redirectable').on('change', function(event, parameters) {
    window.location.href = $(this).val();
});
