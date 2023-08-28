if ($('.sidebar-content-wrapper').length && $('div[class^="page"]').length) {
    $('.sidebar-toggler').css('display','block');
    $(".sidebar-content-wrapper").detach().appendTo("#offCanvasSidebar");
}
