var handle_reload_from = function(_e, data) {
    var el = $(data.selector);

    var url = new Url(el.data('reload-from'));
    var url_selector = el.data('reload-from-selector');

    var has_toggle = el.find('button[data-toggle]').length > 0;
    var toggled = has_toggle && isToggled(el.find('.toggled'));

    // Nobody likes you IE
    url.query.ie_cache_workaround = new Date().getTime();

    el.load(url.toString() + ' ' + url_selector, function() {
        var loaded = $(this);
        loaded = $(loaded.children(':first').unwrap());

        loaded.on('reload-from', handle_reload_from);
        Intercooler.processNodes(loaded);

        _.defer(function() {
            loaded.find('a.confirm').confirmation();
            setupRedirectAfter(loaded.find('a'));
        });

        if (has_toggle) {
            var button = loaded.find('button[data-toggle]');
            button.toggleButton(toggled);
        }
    });
};

$(document).on('reload-from', handle_reload_from);
