$(function () {
    var offCanvasWrap = $('.off-canvas-wrap');
    var target = $('#offCanvasSidebar');
    var toggler = $('.sidebar-toggler');
    var source = $('.sidebar-wrapper').first();

    // Toggler stays hidden unless there is a sidebar to show
    if (!source.children().length || !target.length || !offCanvasWrap.length) {
        return;
    }

    var title = source.data('sidebarMobileTitle');

    if (!title) {
        var headings = source.find('h2, h3');
        title = $.trim(headings.first().text());

        if (headings.length > 2) {
            title += ', ' + $.trim(headings.eq(1).text()) + ', ...';
        } else if (headings.length > 1) {
            title += ' & ' + $.trim(headings.eq(1).text());
        }
    }

    if (title) {
        toggler.attr({'aria-label': title, 'title': title});
        toggler.find('.text').text(title);
    }

    // The content is moved
    var container = $('<div class="offcanvas-sidebar-content"></div>').appendTo(target);
    var desktop = window.matchMedia(
        (window.Foundation && Foundation.media_queries && Foundation.media_queries.medium) ||
        'only screen and (min-width: 40.0625em)'
    );

    function isOpen() {
        return offCanvasWrap.hasClass('move-left');
    }

    function placeSidebar() {
        if (desktop.matches) {
            if (isOpen()) {
                offCanvasWrap.foundation('offcanvas', 'hide', 'move-left');
            }
            container.children().appendTo(source);
        } else {
            source.children().appendTo(container);
        }
    }

    placeSidebar();

    if (desktop.addEventListener) {
        desktop.addEventListener('change', placeSidebar);
    } else {
        desktop.addListener(placeSidebar);
    }

    // The toggler sits outside the wrapper, so it toggles via the API
    toggler.on('click', function (e) {
        e.preventDefault();
        offCanvasWrap.foundation('offcanvas', 'toggle', 'move-left');
    });

    // The menu spans the whole page height, so keep it in the current viewport
    function fitToViewport() {
        target.css({
            top: $(window).scrollTop(),
            bottom: 'auto',
            height: window.innerHeight
        });
    }

    offCanvasWrap.on('open.fndtn.offcanvas', function () {
        fitToViewport();
        target.scrollTop(0);
    });

    $(window).on('scroll resize orientationchange', function () {
        if (isOpen()) {
            fitToViewport();
        }
    });

    // Links close the menu, except toggles that expand more items
    target.on('click', 'a, .offcanvas-sidebar-close', function () {
        if ($(this).closest('.more-items').length) {
            return;
        }
        offCanvasWrap.foundation('offcanvas', 'hide', 'move-left');
    });

    toggler.addClass('is-available');
});