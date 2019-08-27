$('.chosen-select').chosen({
    search_contains: true,
    width: '100%'
}).on('show', function() {
    $(this).hide();
});
