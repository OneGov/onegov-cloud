if ($('.sidebar-content-wrapper').length){
    $('.sidebar-toggler').css('display','block');
    $(".sidebar-content-wrapper").clone().appendTo("#offCanvasSidebar");
}
