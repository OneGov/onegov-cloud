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
        return "https://img.youtube.com/vi/" + id + "/maxresdefault.jpg";
    }

    if (host.match(/vimeo\.com/gi)) {
        return "https://i.vimecodn.com/video/" + id + "_1280jpg";
    }

    return null;
};

var getVideoUrl = function(host, id) {
    if (host.match(/youtube\.com/gi)) {
        return "https://www.youtube.com/embed/" + id + '?autoplay=1';
    }

    if (host.match(/vimeo\.com/gi)) {
        return "https://player.vimeo.com/video/" + id;
    }

    return null;
};

var getVideoInfo = function(link) {
    var info = getVideoId(link.attr('href'));

    if (info) {
        info.thumbnail = getVideoThumbnail(info.host, info.id);
        info.url = getVideoUrl(info.host, info.id);
        info.width = 640;
        info.height = 360;

        return info;
    }

    return null;
};

var VideoFrame = function(link) {
    var info = getVideoInfo(link);

    var iframe = $('<iframe class="video-frame" src="' + info.url + '">')
        .attr('frameborder', '0')
        .attr('allowfullscreen', true)
        .attr('width', info.width)
        .attr('height', info.height);

    var thumb = $('<img class="video-thumbnail" />')
        .on('error', function() {
            $(this).removeAttr('src');
        })
        .on('load', function() {
            $(this).parent().css('height', $(this).height());
        });

    var button = $('<i class="video-button fa fa-play"></i>');

    button.click(function() {
        button.remove();
        thumb.replaceWith(iframe);
    });

    thumb.click(function() {
        button.remove();
        thumb.replaceWith(iframe);
    });

    link.replaceWith(thumb);
    thumb.after(button);
    thumb.attr('src', info.thumbnail);
};

jQuery.fn.videoframe = function() {
    return this.each(function() {
        VideoFrame($(this));
    });
};
