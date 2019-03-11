var initBarChart = function(el) {
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: dataurl }).done(function(data) {
        var chart = barChart({
            data: data,
            interactive: true
        })(el);

        var embedLink = $(el).data('embed-link');
        var embedSource = $(el).data('embed-source');
        if (embedLink && embedSource) {
            appendEmbedCode(
                el,
                '100%',
                chart.height() + 50,
                embedSource,
                embedLink
            );
        }
    });
};

var initSankeyChart = function(el) {
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: dataurl }).done(function(data) {
        var inverse = $(el).data('inverse');
        var chart = sankeyChart({
            data: data,
            interactive: true,
            inverse: inverse
        })(el);

        var embedLink = $(el).data('embed-link');
        var embedSource = $(el).data('embed-source');
        if (embedLink && embedSource) {
            appendEmbedCode(
                el,
                '100%',
                chart.height() + 50,
                embedSource,
                embedLink
        );
        }
    });
};

var initGroupedChart = function(el) {
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: dataurl }).done(function(data) {
        var chart = groupedChart({
            data: data,
            interactive: true
        })(el);

        var embedLink = $(el).data('embed-link');
        var embedSource = $(el).data('embed-source');
        if (embedLink && embedSource) {
            appendEmbedCode(
                el,
                '100%',
                chart.height(),
                embedSource,
                embedLink
            );
        }
    });
};

var initEntitiesMap = function(el) {
    var mapurl = $(el).data('mapurl');
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: mapurl }).done(function(mapdata) {
        $.ajax({ url: dataurl }).done(function(data) {
            var canton = $(el).data('canton');
            var thumbs = $(el).data('thumbs');
            var colorScale = $(el).data('color-scale');
            var labelLeftHand = $(el).data('label-left-hand');
            var labelRightHand = $(el).data('label-right-hand');
            var labelExpats = $(el).data('label-expats');
            var map = entitiesMap({
                mapdata: mapdata,
                data: data,
                canton: canton,
                interactive: true,
                thumbs: thumbs,
                colorScale: colorScale,
                labelLeftHand: labelLeftHand,
                labelRightHand: labelRightHand,
                labelExpats: labelExpats
            })(el);
            $(el).data('map', map);

            var embedLink = $(el).data('embed-link');
            var embedSource = $(el).data('embed-source');
            if (embedLink && embedSource) {
                var ratio = map.width() / map.height();
                appendEmbedCode(el, 500, Math.floor(500 / ratio), embedSource, embedLink);
            }
        });
    });
};


var initDistrictsMap = function(el) {
    var mapurl = $(el).data('mapurl');
    var dataurl = $(el).data('dataurl');
    $.ajax({ url: mapurl }).done(function(mapdata) {
        $.ajax({ url: dataurl }).done(function(data) {
            var canton = $(el).data('canton');
            var thumbs = $(el).data('thumbs');
            var colorScale = $(el).data('color-scale');
            var labelLeftHand = $(el).data('label-left-hand');
            var labelRightHand = $(el).data('label-right-hand');
            var labelExpats = $(el).data('label-expats');
            var map = districtsMap({
                mapdata: mapdata,
                data: data,
                canton: canton,
                interactive: true,
                thumbs: thumbs,
                colorScale: colorScale,
                labelLeftHand: labelLeftHand,
                labelRightHand: labelRightHand,
                labelExpats: labelExpats
            })(el);
            $(el).data('map', map);

            var embedLink = $(el).data('embed-link');
            var embedSource = $(el).data('embed-source');
            if (embedLink && embedSource) {
                var ratio = map.width() / map.height();
                appendEmbedCode(el, 500, Math.floor(500 / ratio), embedSource, embedLink);
            }
        });
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
        $('.entities-map').each(function(ix, el) {
            initEntitiesMap(el);
        });
        $('.districts-map').each(function(ix, el) {
            initDistrictsMap(el);
        });
        $('.map-data-select').each(function(ix, el) {
            $(el).change(function() {
                var dataurl = $(this).val();
                $('.entities-map,.districts-map').each(function(ix, el) {
                    $(el).data('dataurl', dataurl);

                    var map = $(el).data('map');
                    if (map) {
                        map.update(dataurl);
                    }
                });
            });
        });
    });
})(jQuery);
