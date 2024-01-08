var header_height = $('.nav-bar-sticky').height();

var content_lc = $('#content > .grid-x > div:first-child > *:last-child');
var content_bottom = content_lc.offset().top + content_lc.height();

var sidebar_lc = $('.sidebar-wrapper > *:last-child');
var sidebar_bottom = sidebar_lc.offset().top + sidebar_lc.height();

jQuery(document).ready(function() {
  if (content_bottom > sidebar_bottom) {
    jQuery('.content, .sidebar').theiaStickySidebar({
      additionalMarginTop: header_height
    });
  }
});