$(document).ready(function() {
    var pswpElement = document.querySelectorAll('.pswp')[0];
    var images = [];
    var elements = document.querySelectorAll('.photoswipe img');

    var get_thumbs_boundary = function(index) {
        var thumbnail = document.querySelectorAll('.photoswipe img')[index];
        var pageYScroll = window.pageYOffset || document.documentElement.scrollTop;
        var rect = thumbnail.getBoundingClientRect();
        return {x: rect.left, y: rect.top + pageYScroll, w: rect.width};
    };

    var adjust_caption = function() {
        var gallery = this;

        var width = gallery.currItem.w;
        var height = gallery.currItem.h;

        if (gallery.currItem.fitRatio < 1) {
            width = width * gallery.currItem.fitRatio;
            height = height * gallery.currItem.fitRatio;
        }

        windowheight = Math.max(
            document.documentElement.clientHeight,
            window.innerHeight || 0
        );

        $('.pswp__caption__center').width(width);
        $('.pswp__caption').css('top', (windowheight - height) / 2 + height);
    };

    var new_click_handler = function(index) {
        return function() {
            var gallery = new PhotoSwipe(
                pswpElement,
                PhotoSwipeUI_Default,
                images,
                {
                    index: index,
                    zoomEl: false,
                    shareEl: false,
                    getThumbBoundsFn: get_thumbs_boundary
                }
            );

            gallery.listen('afterChange', $.proxy(adjust_caption, gallery));
            gallery.listen('resize', $.proxy(adjust_caption, gallery));
            gallery.init();
        };
    };

    for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        $(el).click(new_click_handler(i));

        var item = {
            src: (el.dataset.src || el.src).replace('/thumbnail', ''),
            w: parseInt((el.dataset.fullWidth || el.attributes.width.value), 10),
            h: parseInt((el.dataset.fullHeight || el.attributes.height.value), 10),
            title: el.alt,
            msrc: (el.dataset.src || el.src)
        };

        images.push(item);
    }
});
