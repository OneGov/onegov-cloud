$(function () {
    var offCanvasWrap = $('.off-canvas-wrap');
    var target = $('#offCanvasSidebar');
    var toggler = $('.sidebar-toggler');
    var source = $('.sidebar-wrapper').first();

    // Toggler stays hidden unless there is a sidebar to copy
    if (!source.length || !target.length || !offCanvasWrap.length) {
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

    var gridClass = /^(columns?|(small|medium|large|xlarge|xxlarge)-(\d+|offset-\d+|push-\d+|pull-\d+|centered|uncentered))$/;
    var visibilityClass = /^(show|hide)-for-[\w-]+$/;

    function removeClasses(el, patterns) {
        var classes = (el.getAttribute('class') || '').split(/\s+/);
        el.setAttribute('class', $.grep(classes, function (cls) {
            return cls && !$.grep(patterns, function (p) { return p.test(cls); }).length;
        }).join(' '));
    }

    var content = source.clone(true);

    // Root: drop grid and visibility classes; inside: only visibility classes
    removeClasses(content[0], [gridClass, visibilityClass]);
    content.find('[class*="show-for-"], [class*="hide-for-"]').each(function () {
        removeClasses(this, [visibilityClass]);
    });

    content = $('<div class="offcanvas-sidebar-content"></div>').append(content);

    // Avoid duplicate IDs
    content.find('[id]').each(function () {
        this.id = this.id + '-mobile';
    });
    content.find('label[for]').each(function () {
        $(this).attr('for', $(this).attr('for') + '-mobile');
    });

    target.append(content);

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

    function isOpen() {
        return offCanvasWrap.hasClass('move-left');
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

    target.on('click', 'a, .offcanvas-sidebar-close', function () {
        offCanvasWrap.foundation('offcanvas', 'hide', 'move-left');
    });

    toggler.addClass('is-available');
});