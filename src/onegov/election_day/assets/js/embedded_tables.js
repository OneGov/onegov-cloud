var createTableEmbedLink = function(el)  {
    var embedLink = $(el).data('embed-link');
    var embedSource = $(el).data('embed-source');
    if (embedLink && embedSource) {
        appendEmbedCode(el, '50%', 200, embedSource, embedLink);
    }
};

(function($) {
    $(document).ready(function() {
        $('.embedded-table').each(function(ix, el) {
            createTableEmbedLink(el);
        });
    });
})(jQuery);