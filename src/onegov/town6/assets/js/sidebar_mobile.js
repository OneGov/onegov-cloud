$('#offCanvasSidebar a').click(function() { $('.off-canvas').foundation('close'); });

if (!$('.sidebar-wrapper').length) {
    $('.sidebar-toggler').css('display', 'none');
}
$(".sidebar-wrapper").clone().appendTo("#offCanvasSidebar");
