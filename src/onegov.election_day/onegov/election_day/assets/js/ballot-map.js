var is_ie = function() {
    var ua = window.navigator.userAgent;

    var msie = ua.indexOf('MSIE ');
    if (msie > 0) {
        // IE 10 or older => return version number
        return parseInt(ua.substring(msie + 5, ua.indexOf('.', msie)), 10);
    }

    var trident = ua.indexOf('Trident/');
    if (trident > 0) {
        // IE 11 => return version number
        var rv = ua.indexOf('rv:');
        return parseInt(ua.substring(rv + 3, ua.indexOf('.', rv)), 10);
    }

    var edge = ua.indexOf('Edge/');
    if (edge > 0) {
       // IE 12 => return version number
       return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10);
    }

    // other browser
    return false;
};

var init_ballot_map = function(el) {

    var map = $(el);
    var path = d3.geo.path().projection(null);
    var svg = d3.select(el).append('svg')
        .attr('xmlns', "http://www.w3.org/2000/svg")
        .attr('version', '1.1');

    svg.append('defs')
       .append('pattern')
           .attr('id', 'uncounted')
           .attr('patternUnits', 'userSpaceOnUse')
           .attr('width', 4)
           .attr('height', 4)
       .append('path')
           .attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
           .attr('stroke', '#999')
           .attr('stroke-width', 1);

    var mapurl = map.data('mapurl');
    var dataurl = map.data('dataurl');
    var canton = map.data('canton');

    var scale = d3.scale.linear()
                .domain([30, 49.9999999, 50.000001, 70])
                .range([
                    "#ca0020",
                    "#f4a582",
                    "#92c5de",
                    "#0571b0"
                ]);

    var tooltip = d3.tip()
        .attr('class', 'd3-tip')
        .direction(function(d) {
            var b = this.getBBox();
            var p = this.parentNode.getBBox();
            return ((b.y - p.y > p.y + p.height - b.y - b.height) ? 'n' : 's') +
                   ((b.x - p.x > p.x + p.width - b.x - b.width) ? 'w' : 'e');
        })
        .html(function(d) {

            if (_.isUndefined(d.properties.result.yeas_percentage)) {
                return '<strong>' + d.properties.name + '</strong>';
            }

            var yeas_percentage =  Math.round(
                d.properties.result.yeas_percentage * 100) / 100;

            var nays_percentage =  Math.round(
                d.properties.result.nays_percentage * 100) / 100;

            // use symbols to avoid text which we would have to translate
            // also, only show the winning side, not both
            if (yeas_percentage > nays_percentage) {
                return [
                    '<strong>' + d.properties.name + '</strong>',
                    '<i class="fa fa-thumbs-up"></i> ' + yeas_percentage + '%'
                ].join('<br/>');
            } else {
                return [
                    '<strong>' + d.properties.name + '</strong>',
                    '<i class="fa fa-thumbs-down"></i> ' + nays_percentage + '%'
                ].join('<br/>');
            }
        });

    // load the map and then the data
    $.ajax({ url: mapurl }).done(function(mapdata) {
        $.ajax({ url: dataurl }).done(function(data) {
            svg.append('g')
                .attr('class', 'municipality')
                .style('fill', 'transparent')
                .selectAll('path')
                .data(
                    topojson.feature(
                        mapdata, mapdata.objects.municipalities).features
                )
                .enter().append('path')
                .attr('d', path)
                .attr('fill', function(d) {

                    // store the result for the tooltip
                    d.properties.result = data[d.properties.id];

                    if (! _.isUndefined(d.properties.result)) {
                        if (d.properties.result.counted) {
                            return scale(d.properties.result.yeas_percentage);
                        } else {
                            return 'url(#uncounted)';
                        }
                    }
                })
                .attr('class', function(d) {
                    if (! _.isUndefined(d.properties.result)) {
                        if (d.properties.result.counted) {
                            return 'counted';
                        } else {
                            return 'uncounted';
                        }
                    }
                })
                .on('mouseover', tooltip.show)
                .on('mouseout', tooltip.hide);

            if (mapdata.objects.lakes !== undefined) {
                svg.append('g')
                    .attr('class', 'lake')
                    .style('fill', '#FFF')
                    .style('stroke', '#999')
                    .style('stroke-width', '1px')
                    .selectAll('path')
                    .data(
                        topojson.feature(
                            mapdata, mapdata.objects.lakes).features
                    )
                    .enter().append('path')
                    .attr('d', path);
            }

            svg.append('path')
                .datum(topojson.mesh(
                    mapdata, mapdata.objects.municipalities, function(a, b) {
                        return a !== b;
                    }
                ))
                .attr('class', 'border')
                .style('stroke-width', '1px')
                .style('fill', 'none')
                .attr('d', path);

            var legend_values = [80, 70, 60, 50.001, 49.999, 40, 30, 20];

            var color_scale = _.map(legend_values, function(value) {
                return scale(value);
            });

            var legend_items = _.map(color_scale, function(color) {
                return $('<li />').css('border-top', '10px solid ' + color);
            });

            var legend = map.find('.legend');
            legend.append($('<ul />').append(legend_items));
            legend.append($('<div class="clearfix"></div>'));
            legend.append($('<div class="legend-left">' + legend.data('left-hand') + '</div>'));
            legend.append($('<div class="legend-right">' + legend.data('right-hand') + '</div>'));

            map.append(legend);

            // set the svg element size to the bounding box, to avoid extra
            // whitespace around the map
            var bbox = svg[0][0].getBBox();

            svg.attr('viewBox',
                [bbox.x, bbox.y, bbox.width, bbox.height].join(' ')
            );

            // browsers other than ie figure out a nice size by themselves
            if (is_ie()) {
                svg.attr('width', 470);
                svg.attr('height', 470 * (bbox.height/bbox.width));
            }

            svg.call(tooltip);

            // move each element up when it's selected (there's no z-index in
            // svg) and make sure the others are deselected
            map.find('.municipality path').each(function(ix, path) {
                $(path).on('mouseenter', function() {
                    $('.municipality path.selected').each(
                        function() {
                            $(this).removeClass('selected');
                        }
                    );
                    $(this).attr('class', $(this).attr('class') + ' selected');
                    $(this).parent(this).prepend(this);
                });
                $(path).on('mouseleave', function() {
                    $(this).attr('class', $(this).attr('class').replace('selected', ''));
                });
            });

            var download_link = $(el).data('download-link');
            if (download_link) {
                append_svg_download_link(el, $(el).find('svg')[0].outerHTML, 'map', download_link);
            }

            var embed_link = $(el).data('embed-link');
            var embed_source = $(el).data('embed-source');
            if (embed_link && embed_source) {
                var height = Math.floor(500 * (bbox.height/bbox.width)) + 70;
                append_embed_code(el, 500, height, embed_source, embed_link);
            }
        });
    });
};

(function($) {
    $(document).ready(function() {
        $('.ballot-map').each(function(ix, el) {
            init_ballot_map(el);
        });
    });
})(jQuery);
