if (!$('.sidebar-content-wrapper').length) {
    $('.sidebar-toggler').css('display', 'none');
}

if ($('.sidebar-toggler').css('display') == 'block') {
    $(".sidebar-content-wrapper").detach().appendTo("#offCanvasSidebar");
}