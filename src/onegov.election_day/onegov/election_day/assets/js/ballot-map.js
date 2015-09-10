var init_ballot_map = function(el) {

    var map = $(el);
    var path = d3.geo.path().projection(null);
    var svg = d3.select(el).append('svg');

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
        .offset([-10, 0])
        .html(function(d) {

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
    d3.json(mapurl, function(error, mapdata) {
        d3.json(dataurl, function(error, data) {

            svg.append('g')
                .attr('class', 'municipality')
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
                        return scale(d.properties.result.yeas_percentage);
                    }
                })
                .on('mouseover', tooltip.show)
                .on('mouseout', tooltip.hide);

            if (mapdata.objects.lakes !== undefined) {
                svg.append('g')
                    .attr('class', 'lake')
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
                    $(this).attr('class', 'selected');
                    $(this).parent(this).prepend(this);
                });
                $(path).on('mouseleave', function() {
                    $(this).attr('class', '');
                });
            });
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
