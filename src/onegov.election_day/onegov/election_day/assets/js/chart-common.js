var append_svg_download_link = function(target, data, title, text) {
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

var append_embed_code = function(target, width, height, source, title) {
    var id = 'embed_code_' + Math.floor(Math.random() * 100) + 1;
    $(target).append(
        $('<div>')
        .attr('class', 'embed')
        .append(
            $('<a>')
            .attr('href', '#')
            .on('click', function() {
               $('#'+id).toggle();
               return false;
            })
            .text(title)
            .prepend(
                $('<i>')
                .attr('class', 'fa fa-share-square-o')
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
