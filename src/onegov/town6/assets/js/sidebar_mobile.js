$('#offCanvasSidebar').on('click', 'a', function() {
    $('.off-canvas').foundation('close');
});

if (!$('.sidebar-wrapper').length) {
    $('.sidebar-toggler').css('display', 'none');
}

newSidebarTitle = $('#right-sidebar').data("sidebarMobileTitle");
// Take the text of the first two h3 elements in the sidebar and use them as the title
if (!newSidebarTitle) {
    newSidebarTitle = $('.sidebar-wrapper h3').first().text();
    if ($('.sidebar-wrapper h3').length > 2) {
        newSidebarTitle += ", " + $('.sidebar-wrapper h3').eq(1).text();
        newSidebarTitle += ", ...";
    } else if ($('.sidebar-wrapper h3').length > 1) {
        newSidebarTitle += " & " + $('.sidebar-wrapper h3').eq(1).text();
    }
    $('.sidebar-toggler span.text').text(newSidebarTitle);
}
if (newSidebarTitle) {
    $('.sidebar-toggler span.text').text(newSidebarTitle);
}

$(".sidebar-wrapper").clone().appendTo("#offCanvasSidebar");
