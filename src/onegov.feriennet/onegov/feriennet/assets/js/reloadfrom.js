var handle_reload_from = function(_e, data) {
    var el = $(data.selector);

    var url = new Url(el.data('reload-from'));
    var url_selector = el.data('reload-from-selector');

    var expand = el.find('.toggled').length > 0 && true || false;

    if (!expand && _.has(url.query, 'expand')) {
        delete url.query.expand;
    } else if (expand) {
        url.query.expand = '1';
    }

    // Nobody likes you IE
    url.query.ie_cache_workaround = new Date().getTime();

    el.load(url.toString() + ' ' + url_selector, function() {
        var loaded = $(this);
        loaded = $(loaded.children(':first').unwrap());

        loaded.on('reload-from', handle_reload_from);
        Intercooler.processNodes(loaded);
        loaded.find('button[data-toggle]').toggleButton();
    });
};

$(document).on('reload-from', handle_reload_from);

