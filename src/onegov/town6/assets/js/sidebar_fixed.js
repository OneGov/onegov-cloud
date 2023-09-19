if ($('.sidebar-content-wrapper').length){

    var header_height = $('.nav-bar-sticky').height();
    var footer_height = $('#footer').height();

    var content_lc = $('#content > .grid-x > div:first-child > *:last-child');
    var content_bottom = content_lc.offset().top + content_lc.height();

    var sidebar_lc = $('.sidebar > *:last-child');
    var sidebar_bottom = sidebar_lc.offset().top + sidebar_lc.height();

    if (content_bottom > sidebar_bottom) {
        $('.sidebar-wrapper').stickySidebar({
            topSpacing: header_height,
            innerWrapperSelector: '.sidebar-content-wrapper'
        });

    }
}
