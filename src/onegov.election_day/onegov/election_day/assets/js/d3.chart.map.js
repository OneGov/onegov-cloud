//
// A map.
//
(function(root, factory) {
  if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = factory;
  } else {
    root.ballotMap = factory(root.d3, root.topojson);
  }
}(this, function(d3, topojson) {
    return function(params) {
        var data = {};
        var mapdata = {};
        var canton = '';
        var margin = {top: 20, right: 10, bottom: 20, left: 10};
        var height = 0;
        var width = 0;
        var interactive = false;
        var yay = 'Yay';
        var nay = 'Nay';
        var options = {
            legendHeight: 10,
            legendMargin: 30,
            fontSizePx: 14,
            fontFamily: 'sans-serif',
        };

        if (params) {
            if (params.data) data = params.data;
            if (params.mapdata) mapdata = params.mapdata;
            if (params.canton) canton = params.canton;
            if (params.interactive) interactive = params.interactive;
            if (params.width) width = params.width;
            if (params.yay) yay = params.yay;
            if (params.nay) nay = params.nay;
            if (params.options) options = params.options;
        }

        var isUndefined = function(obj) {
            return obj === void 0;
        };

        var chart = function(container) {

            // Try to read a default width from the container if none is given
            if ((typeof $ !== 'undefined') && !width) {
                width = $(container).width();
            }

            var svg = d3.select(container).append('svg')
                .attr('xmlns', 'http://www.w3.org/2000/svg')
                .attr('version', '1.1')
                .attr('width', width);

            if (data && mapdata.transform) {

                var path = d3.geo.path().projection(null);

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

                var scale = d3.scale.linear()
                    .domain([30, 49.9999999, 50.000001, 70])
                    .range(['#ca0020', '#f4a582', '#92c5de', '#0571b0']);

                // Add tooltips
                var tooltip = null;
                if (interactive) {
                    tooltip = d3.tip()
                        .attr('class', 'd3-tip')
                        .direction(function(d) {
                            var b = this.getBBox();
                            var p = this.parentNode.getBBox();
                            return ((b.y - p.y > p.y + p.height - b.y - b.height) ? 'n' : 's') +
                                   ((b.x - p.x > p.x + p.width - b.x - b.width) ? 'w' : 'e');
                        })
                        .html(function(d) {
                            if (isUndefined(d.properties.result.yeas_percentage)) {
                                return '<strong>' + d.properties.name + '</strong>';
                            }
                            var yeas_percentage =  Math.round(d.properties.result.yeas_percentage * 100) / 100;
                            var nays_percentage =  Math.round(d.properties.result.nays_percentage * 100) / 100;

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
                }

                // Add municipalties
                mapdata.transform.translate=[0,0];
                var municipalities = svg.append('g')
                    .attr('class', 'municipality')
                    .style('fill', 'transparent')
                    .selectAll('path')
                    .data(
                        topojson.feature(mapdata, mapdata.objects.municipalities).features
                    )
                    .enter().append('path')
                    .attr('d', path)
                    .attr('fill', function(d) {
                        // store the result for the tooltip
                        d.properties.result = data[d.properties.id];
                        if (!isUndefined(d.properties.result)) {
                            if (d.properties.result.counted) {
                                return scale(d.properties.result.yeas_percentage);
                            } else {
                                return 'url(#uncounted)';
                            }
                        }
                    })
                    .attr('class', function(d) {
                        if (!isUndefined(d.properties.result)) {
                            if (d.properties.result.counted) {
                                return 'counted';
                            } else {
                                return 'uncounted';
                            }
                        }
                    });
                if (interactive) {
                    municipalities
                        .on('mouseover', tooltip.show)
                        .on('mouseout', tooltip.hide)
                        .on('click', tooltip.show);
                }

                // Add lakes
                if (mapdata.objects.lakes !== undefined) {
                    svg.append('g')
                        .attr('class', 'lake')
                        .style('fill', '#FFF')
                        .style('stroke', '#999')
                        .style('stroke-width', '1px')
                        .selectAll('path')
                        .data(
                            topojson.feature(mapdata, mapdata.objects.lakes).features
                        )
                        .enter().append('path')
                        .attr('d', path);
                }

                // Add Borders
                svg.append('g')
                    .append('path')
                    .datum(topojson.mesh(
                        mapdata, mapdata.objects.municipalities, function(a, b) {
                            return a !== b;
                        }
                    ))
                    .attr('class', 'border')
                    .style('stroke-width', '1px')
                    .style('fill', 'none')
                    .attr('d', path);

                // Add the legend (we need to up/downscale the elements)
                var bboxMap = svg[0][0].getBBox();
                var unitScale = d3.scale.linear()
                    .rangeRound([0, bboxMap.width / (width - margin.left - margin.right)]);
                var legendValues = [80, 70, 60, 50.001, 49.999, 40, 30, 20];
                var legendScale = d3.scale.ordinal()
                    .domain(legendValues)
                    .rangeRoundBands([0.2 * bboxMap.width, 0.8 * bboxMap.width]);
                var legend = svg.append('g')
                    .attr('transform', function(d) {
                        return 'translate(0,' + unitScale(options.legendMargin) + ')';
                    });
                var legendItems = legend.selectAll('.legend_item')
                    .data(legendValues).enter()
                    .append('rect')
                    .attr('x', function(d) {return legendScale(d);})
                    .attr('width', legendScale.rangeBand())
                    .attr('height', unitScale(options.legendHeight))
                    .style('fill', function(d) {return scale(d);});
                var text_yay = legend.append('text')
                    .attr('x', legendScale(80))
                    .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                    .style('font-size', unitScale(options.fontSizePx) + 'px')
                    .style('font-family', options.fontFamily)
                    .text(yay);
                var text_nay = legend.append('text')
                    .attr('x', legendScale(20) + legendScale.rangeBand())
                    .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                    .style('text-anchor', 'end')
                    .style('font-size',unitScale(options.fontSizePx) + 'px')
                    .style('font-family', options.fontFamily)
                    .text(nay);

                // Set size
                bbox = svg[0][0].getBBox();
                height = Math.floor(width * (bbox.height/bbox.width));
                svg.attr('height', height)
                   .attr('viewBox',
                    [
                      bbox.x - unitScale(margin.left),
                      bbox.y - unitScale(margin.top),
                      bbox.width + unitScale(margin.left) + unitScale(margin.right),
                      bbox.height + unitScale(margin.top) + unitScale(margin.bottom)
                    ].join(' ')
                );


                if (interactive) {
                    // move each element up when it's selected (there's no z-index in
                    // svg) and make sure the others are deselecte
                    $(container).find('.municipality path').each(function(ix, path) {
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

                    // Add tooltips
                    svg.call(tooltip);

                    // Relayout on resize
                    d3.select(window).on('resize.ballotmap', function() {
                        width = $(container).width();
                        unitScale.rangeRound([0, bboxMap.width / (width - margin.left - margin.right)]);
                        legendScale.rangeRoundBands([0.2 * bboxMap.width, 0.8 * bboxMap.width]);
                        legend.attr('transform', function(d) {
                                return 'translate(0,' + unitScale(options.legendMargin) + ')';
                            });
                        legendItems.attr('x', function(d) {return legendScale(d);})
                            .attr('width', legendScale.rangeBand())
                            .attr('height', unitScale(options.legendHeight))
                            .style('fill', function(d) {return scale(d);});
                        text_yay.attr('x', legendScale(80))
                            .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                            .style('font-size', unitScale(options.fontSizePx) + 'px');
                        text_nay.attr('x', legendScale(20) + legendScale.rangeBand())
                            .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                            .style('font-size', unitScale(options.fontSizePx) + 'px');

                        bbox = svg[0][0].getBBox();

                        height = Math.floor(width * (bbox.height/bbox.width));


                        svg.attr('width', width)
                           .attr('height', height)
                           .attr('viewBox',
                            [
                              bbox.x - unitScale(margin.left),
                              bbox.y - unitScale(margin.top),
                              bbox.width + unitScale(margin.left) + unitScale(margin.right),
                              bbox.height + unitScale(margin.top) + unitScale(margin.bottom)
                            ].join(' ')
                        );
                    });
                }
            }
            return chart;
        };

        chart.width = function() {
            return width;
        };

        chart.height = function() {
            return height;
        };

        return chart;
    };
}));
