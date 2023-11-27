if ($('.sidebar-content-wrapper').length){
$(window).on("load", function() {

    var header_height = $('.nav-bar-sticky').height();

    var content_lc = $('#content > .grid-x > div:first-child > *:last-child');
    var content_bottom = content_lc.offset().top + content_lc.height();

    var sidebar_lc = $('.sidebar-content-wrapper > *:last-child');
    var sidebar_bottom = sidebar_lc.offset().top + sidebar_lc.height();

    console.log('content', content_lc)
    console.log('content height', content_bottom)
    console.log('sidebar', sidebar_lc)
    console.log('sidebar height', sidebar_bottom)

    if (content_bottom > sidebar_bottom) {
        $('.sidebar-wrapper').stickySidebar({
            topSpacing: header_height,
            innerWrapperSelector: '.sidebar-content-wrapper'
        });
    }
})
}
