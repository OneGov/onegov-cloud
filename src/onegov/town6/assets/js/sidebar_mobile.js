
// detect if window is resized
$(window).resize(function() {
    if (!$('.sidebar-wrapper').length) {
        $('.sidebar-toggler').css('display', 'none');
        $(".sidebar-wrapper").detach().appendTo("#right-sidebar");
    }
    if ($('.sidebar-toggler').css('display') === 'block') {
        $(".sidebar-wrapper").detach().appendTo("#offCanvasSidebar");
        $('.off-canvas a').click(function() { $('.off-canvas').foundation('close'); });
    }
});
