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

var getVideoThumbnail = function(host, id) {
    if (host.match(/youtube\.com/gi)) {
        return "https://img.youtube.com/vi/" + id + "/hqdefault.jpg";
    }

    if (host.match(/vimeo\.com/gi)) {
        return "https://i.vimecodn.com/video/" + id + "_640jpg";
    }

    return null;
};

var getVideoInfo = function(link) {
    var info = getVideoId(link.attr('href'));

    if (info) {
        info.thumbnail = getVideoThumbnail(info.host, info.id);
        info.url = link.attr('href').replace('http://', 'https://');
        info.width = 640;
        info.height = 360;

        return info;
    }

    return null;
};

var VideoFrame = function(link) {
    var info = getVideoInfo(link);

    var iframe = $('<iframe class="video-frame" src="' + info.url + '">')
        .attr('autoplay', '1')
        .attr('frameborder', '0')
        .attr('allowfullscreen', true)
        .attr('width', info.width)
        .attr('height', info.height);

    var thumb = $('<img class="video-thumbnail" src="' + info.thumbnail + '">')
        .append('<div class="video-play />');

    thumb.click(function() {
        thumb.replaceWith(iframe);
    });

    link.replaceWith(thumb);
};

jQuery.fn.videoframe = function() {
    return this.each(function() {
        VideoFrame($(this));
    });
};
