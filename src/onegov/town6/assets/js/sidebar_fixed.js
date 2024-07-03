var header_height = $('.nav-bar-sticky').height();

if ($('#content > .grid-x > div:first-child > *:first-child').length) {
  content_lc = $('#content > .grid-x > div:first-child > *:first-child');
  var content_bottom = content_lc.offset().top + content_lc.height();

  if ($('.sidebar-wrapper > *:first-child').length) {
    sidebar_lc = $('.sidebar-wrapper > *:first-child');
    var sidebar_bottom = sidebar_lc.offset().top + sidebar_lc.height();

    jQuery(document).ready(function() {
      if (content_bottom > sidebar_bottom) {
        jQuery('.content, .sidebar').theiaStickySidebar({
          additionalMarginTop: header_height
        });
      };
    });
  };
};
