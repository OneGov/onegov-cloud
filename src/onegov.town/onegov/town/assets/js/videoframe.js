/*
    Scans the page for youtube links (annotated with the 'has-video' class) and
    turns them into iframes. This means we don't have to loosen our content
    security policy and we don't load anything until the user clicks on a
    video (which is good for the mobile).
*/

var expressions = [
    /https?:\/\/(www\.youtube\.com)\/watch\?v=([^&]+)/i,
    /https?:\/\/(www\.vimeo\.com)\/([0-9]+)/i
];

var getVideoId = function(url) {
    for (var i = 0; i < expressions.length; i++) {
        var match = url.match(expressions[i]);

        if (match) {
            return {
                'host': match[1],
                'id': match[2]
            };
        }
    }

    return null;
};

var getVideoUrl = function(host, id) {
    if (host.match(/youtube\.com/gi)) {
        var origin = window.location.protocol +
        '//' + window.location.host +
        (window.location.port && (':' + window.location.port));

        return "https://www.youtube.com/embed/" + id + '?modestbranding=1&showinfo=0&origin=' + origin;
    }

    if (host.match(/vimeo\.com/gi)) {
        return "https://player.vimeo.com/video/" + id;
    }

    return null;
};

var getVideoInfo = function(link) {
    var info = getVideoId(link.attr('href'));

    if (info) {
        info.url = getVideoUrl(info.host, info.id);
        return info;
    }

    return null;
};

var VideoFrame = function(link) {
    var info = getVideoInfo(link);
    var parent = link.parent();

    var wrapper = $('<div class="video-wrapper" />');

    var iframe = $('<iframe class="video-frame" src="' + info.url + '">')
        .attr('frameborder', '0')
        .on('load', function() {
            parent.css('min-height', '0');
            parent.find('br').remove();
        });

    link.replaceWith(wrapper.append(iframe));
};

jQuery.fn.videoframe = function() {
    return this.each(function() {
        VideoFrame($(this));
    });
};
