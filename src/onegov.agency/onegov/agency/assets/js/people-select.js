$('.people-select').chosen({
    search_contains: true,
    allow_single_deselect: true,
    width: '100%',
    placeholder_text_single: '-'
}).on('change', function() {
    window.location.href = $(this).val();
});
