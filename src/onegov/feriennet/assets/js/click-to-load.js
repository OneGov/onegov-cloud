/*
Implements click-to-load by providing a link that loads elements from a
source, replaces the target and updates itself with the click-to-load link
from the source.

Click-to-load elements need to have a unique id.

Example:

    <div class="list-of-things">
        ...
    </div>

    <div id="click-to-load-target">

    </div>

    <a class="click-to-load" id="click-to-load"
        href="/next-page"
        data-source="/next-page .list-of-things"
        data-target="#click-to-load-target">
            Load more
    </a>

If an optional element with the id "click-to-load-location" is present on the
loaded page, it's 'data-location' attribute is used to update the location
history.

*/
jQuery.fn.clickToLoad = function() {
    var el = $(this);
    var id = el.attr('id');

    var target = el.data('target');
    var source = el.data('source');

    el.on('click', function(e) {
        var container = $('<div>');

        container.load(source, function(data) {
            $(target).before(container);

            var next = $(data).find('#' + id);
            if (next.length === 0) {
                el.remove();
            } else {
                latest = next;
                target = next.data('target');
                source = next.data('source');
            }

            var location = $(data).find('#' + id + '-location');
            if (location.data('location')) {
                console.log(location.data('location'));
                history.pushState({}, '', location.data('location'));
            }
        });

        e.preventDefault();
    });
};

// hooks the targeted elements up
$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).find('.click-to-load').clickToLoad();
});

$(document).ready(function() {
    $('.click-to-load').clickToLoad();
});
