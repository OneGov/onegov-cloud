var header_height = $('.nav-bar-sticky').height();

jQuery(document).ready(function() {
    jQuery('.content, .sidebar').theiaStickySidebar({
      additionalMarginTop: header_height
    });
  });