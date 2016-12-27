var initBarChart = function(el) {
    var dataurl = $(el).data('dataurl');
    var download_link = $(el).data('download-link');
    var embed_link = $(el).data('embed-link');
    var embed_source = $(el).data('embed-source');

    $.ajax({ url: dataurl }).done(function(data) {
        var chart = barChart({
            data: data,
            width: $(el).width(),
            interactive: true
        })(el);

        if (download_link) {
            appendSvgDownloadLink(el, $(el).html(), data.title, download_link);
        }

        if (embed_link && embed_source) {
            appendEmbedCode(el, '100%', chart.height() + 50, embed_source, embed_link);
        }
    });
};

var initSankeyChart = function(el) {
    var dataurl = $(el).data('dataurl');
    var inverse = $(el).data('inverse');
    var download_link = $(el).data('download-link');
    var embed_link = $(el).data('embed-link');
    var embed_source = $(el).data('embed-source');

    $.ajax({ url: dataurl }).done(function(data) {
        var chart = sankeyChart({
            data: data,
            width: $(el).width(),
            interactive: true,
            inverse: inverse
        })(el);

        if (download_link) {
            appendSvgDownloadLink(el, $(el).html(), data.title, download_link);
        }

        if (embed_link && embed_source) {
            appendEmbedCode(el, '100%', chart.height() + 50, embed_source, embed_link);
        }
    });
};

var initGroupedChart = function(el) {
    var dataurl = $(el).data('dataurl');
    var download_link = $(el).data('download-link');
    var embed_link = $(el).data('embed-link');
    var embed_source = $(el).data('embed-source');

    $.ajax({ url: dataurl }).done(function(data) {
        var chart = groupedChart({
            data: data,
            width: $(el).width(),
            interactive: true
        })(el);

        if (download_link) {
            appendSvgDownloadLink(el, $(el).html(), data.title, download_link);
        }

        if (embed_link && embed_source) {
            appendEmbedCode(el, '100%', chart.height(), embed_source, embed_link);
        }
    });

};

(function($) {
    $(document).ready(function() {
        $('.bar-chart').each(function(ix, el) {
            initBarChart(el);
        });
        $('.grouped-bar-chart').each(function(ix, el) {
            initGroupedChart(el);
        });
        $('.sankey-chart').each(function(ix, el) {
            initSankeyChart(el);
        });
    });
})(jQuery);
