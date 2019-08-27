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

    <a class="#click-to-load"
        href="/next-page"
        data-source="/next-page .list-of-things"
        data-target="#click-to-load-target">
            Load more
    </a>

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
                target = next.data('target');
                source = next.data('source');
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
