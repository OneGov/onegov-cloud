var init_ballot_map = function(el) {

    var map = $(el);
    var path = d3.geo.path().projection(null);
    var svg = d3.select(el).append('svg');

    var mapurl = map.data('mapurl');
    var dataurl = map.data('dataurl');
    var canton = map.data('canton');

    var scale = d3.scale.linear()
                .domain([10, 40, 50, 60, 90])
                .range([
                    "#d7191c",
                    "#fdae61",
                    "#ffffbf",
                    "#abd9e9",
                    "#2c7bb6"
                ]);

    var tooltip = d3.tip()
        .attr('class', 'd3-tip')
        .offset([-10, 0])
        .html(function(d) {

            var yays_percentage =  Math.round(
                d.properties.result.yays_percentage * 100) / 100;

            var nays_percentage =  Math.round(
                d.properties.result.nays_percentage * 100) / 100;

            // use symbols to avoid text which we would have to translate
            // also, only show the winning side, not both
            if (yays_percentage > nays_percentage) {
                return [
                    '<strong>' + d.properties.name + '</strong>',
                    '<i class="fa fa-thumbs-up"></i> ' + yays_percentage + '%'
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
                        return scale(d.properties.result.yays_percentage);
                    }
                })
                .on('mouseover', tooltip.show)
                .on('mouseout', tooltip.hide);

            svg.append('g')
                .attr('class', 'lake')
                .selectAll('path')
                .data(
                    topojson.feature(
                        mapdata, mapdata.objects.lakes).features
                )
                .enter().append('path')
                .attr('d', path);

            svg.append('path')
                .datum(topojson.mesh(
                    mapdata, mapdata.objects.municipalities, function(a, b) {
                        return a !== b; 
                    }
                ))
                .attr('class', 'border')
                .style('stroke-width', '1px')
                .attr('d', path);

            // set the svg element size to the bounding box, to avoid extra
            // whitespace around the map
            var bbox = svg[0][0].getBBox();
            svg.attr('viewBox',
                [bbox.x, bbox.y, bbox.width, bbox.height].join(' ')
            );

            svg.call(tooltip);

            // move each element up when it's selected (there's no z-index in
            // svg) and make sure the others are deselected
            $('.municipality path').each(function(ix, path) {
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
