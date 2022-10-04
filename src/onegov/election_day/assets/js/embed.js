var appendSvgDownloadLink = function(target, data, title, text) {
    if (data) {
        $(target).append(
            $('<a>')
            .attr('class', 'svg-download')
            .attr('href-lang', 'image/svg+xml')
            .attr('href', 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(data))))
            .attr('download', title + '.svg')
            .text(text)
            .prepend(
                $('<i>')
                .attr('class', 'fa fa-download')
            )
        );
    }
};

var appendEmbedCode = function(target, width, height, source, title) {
    var id = 'embed_code_' + Math.floor(Math.random() * 100) + 1;
    $(target).append(
        $('<div>')
        .attr('class', 'embed')
        .append(
            $('<a>')
            .attr('href', '#')
            .attr('aria-expanded', false)
            .attr('id', 'embed-link')
            .on('click', function() {
                embed_link = document.getElementById("embed-link")
                if (embed_link.getAttribute('aria-expanded') == 'false') {
                    embed_link.setAttribute("aria-expanded", true);
                } else {
                    embed_link.setAttribute("aria-expanded", false);
                }
                $('#'+id).toggle();
               return false;
            })
            .text(title)
            .prepend(
                $('<i>')
                .attr('class', 'fa fa-share-square-o')
            )
            .append(
                $('<i>')
                .attr('class', 'fa fa-caret-down')
                .attr('style', 'padding-left: .5rem;')
            )
        )
        .append(
            $('<code>')
            .attr('id', id)
            .css('display', 'none')
            .text(
                '<iframe src="' + source + '" ' +
                'width="' + width + '" ' +
                'height="' + height + '" ' +
                'scrolling="no" frameborder="0"></iframe>'
            )
        )
    );
};
