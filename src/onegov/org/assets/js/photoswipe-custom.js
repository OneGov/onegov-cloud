$(document).ready(function() {
    var pswpElement = document.querySelectorAll('.pswp')[0];
    var images = [];
    var elements = document.querySelectorAll('.photoswipe img');

    if (!pswpElement ||
        !elements.length ||
        typeof PhotoSwipe === 'undefined' ||
        typeof PhotoSwipeUI_Default === 'undefined') {
        return;
    }

    var first_number = function(values, fallback) {
        for (var valueIndex = 0; valueIndex < values.length; valueIndex++) {
            if (values[valueIndex]) {
                return values[valueIndex];
            }
        }
        return fallback;
    };

    var get_caption = function(element) {
        var figure = $(element).closest('figure')[0];
        var caption = figure && figure.querySelector('figcaption');
        return caption ? caption.textContent.trim() : element.alt;
    };

    var get_thumbs_boundary = function(index) {
        var thumbnail = elements[index];
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

        var windowheight = Math.max(
            document.documentElement.clientHeight,
            window.innerHeight || 0
        );

        $('.pswp__caption__center').width(width);
        $('.pswp__caption').css('top', (windowheight - height) / 2 + height);
    };

    var new_click_handler = function(index) {
        return function(event) {
            event.preventDefault();
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

        var imageWidth = first_number([
            parseInt(el.dataset.fullWidth, 10),
            el.naturalWidth,
            parseInt(el.getAttribute('width'), 10),
            Math.round(el.getBoundingClientRect().width)
        ], 1);
        var imageHeight = first_number([
            parseInt(el.dataset.fullHeight, 10),
            el.naturalHeight,
            parseInt(el.getAttribute('height'), 10)
        ], 0);

        if (!imageHeight && el.naturalWidth && el.naturalHeight) {
            imageHeight = Math.round(
                imageWidth * el.naturalHeight / el.naturalWidth
            );
        }

        if (!imageHeight) {
            imageHeight = first_number([
                Math.round(el.getBoundingClientRect().height)
            ], imageWidth);
        }

        var item = {
            src: (el.dataset.src || el.src).replace('/thumbnail', ''),
            w: imageWidth,
            h: imageHeight,
            title: get_caption(el),
            msrc: (el.dataset.src || el.src)
        };

        images.push(item);
    }
});
