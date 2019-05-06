// executed if the root of the iFrame is reached (the 'src' of the iFrame)
$(document).on('load-iframe-root', function() {

});

// executed if a non-root page is reached
$(document).on('load-iframe-page', function() {
    // show the title as h2 above the header (hidden on main pages)
    var title = $('.main-title').text().trim();
    title = $('<h2 class="framed-only">' + title + '</h2>');
    $('.locals').before(title)

    // add a back button
    var breadcrumbs = $('.breadcrumbs li');
    var parent = $(breadcrumbs[breadcrumbs.length - 2]).find('a').attr('href');

    $("h2.framed-only").after(
        '<p class="framed-only"><a class="small" href="' + parent + '">Zurück</a></p>'
    );
});

$(document).ready(function() {
    var url = location.href;
    var ref = document.referrer;

    var hostname = function(href) {
        var parser = document.createElement('a');
        parser.href = href;

        return parser.hostname;
    };

    var pathname = function(href) {
        var parser = document.createElement('a');
        parser.href = href;

        return parser.pathname;
    };

    var normalize = function(href) {
        return hostname(href) + pathname(href);
    };

    // if the referrer and the location are equal, the user navigated inside
    // the iFrame - otherwise he just loaded the page with the iFrame
    if (hostname(url) !== hostname(ref)) {
        sessionStorage.setItem("iframe-root", url);
    }

    var root = sessionStorage.getItem("iframe-root");

    // this should not happen, but if it does for some reason, we assume
    // the current site is the root
    if (typeof root === 'undefined') {
        sessionStorage.setItem("iframe-root", url);
        root = url;
    }

    // finally we can run code on the root and on other sites
    if (normalize(url) === normalize(root)) {
        $(document).trigger('load-iframe-root');
    } else {
        $(document).trigger('load-iframe-page');
    }
});
