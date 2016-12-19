var init_bar_chart = function(el) {

    var margin = {top: 20, right: 10, bottom: 20, left: 10};
    var width = $(el).width() - margin.left - margin.right;
    var height = 400 - margin.top - margin.bottom;
    var options = {
        axisHeight: 30,
        barOuterWidth: 25,
        barInnerWidth: 22,
        tickWidth: 5
    };

    var svg = d3.select(el).append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .attr('xmlns', 'http://www.w3.org/2000/svg')
        .style('shape-rendering', 'crispEdges')
        .attr('version', '1.1');
    var canvas = svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    // Define 4 scales to position the bars:
    // - one to get the x-center of a group
    // - one to get the x-position of the bar in relation to the group
    // - one to get the the y-position of the front bars
    // - one to get the the y-position of the back bars
    var scale = {
        x: d3.scale.ordinal(),
        dx: d3.scale.ordinal(),
        y: {
            front: d3.scale.linear().range([height - options.axisHeight, 0]),
            back: d3.scale.linear().range([height - options.axisHeight, 0])
        }
    };

    var axis = {front: null, back: null, all: null};
    var bar = {front: null, back: null, all: null};
    var label = null;

    $.ajax({ url: $(el).data('dataurl') }).done(function(data) {

        if (data.results && data.labels && data.maximum) {

            // Adjust the scales
            scale.x.domain(data.groups).rangeRoundPoints([0, width], 1.0);
            scale.dx
                .domain(data.labels)
                .rangeRoundBands(
                    [
                        -(data.labels.length * options.barOuterWidth)/2,
                        (data.labels.length * options.barOuterWidth)/2
                    ]
                );
            scale.y.front.domain([0, data.maximum.front]);
            scale.y.back.domain([0, data.maximum.back]);

            // Add the labels
            label = canvas.selectAll('.label')
                .data(data.groups)
                .enter().append('g')
                .attr('class', 'label')
                .attr('transform', function(d) {
                    return 'translate(' + scale.x(d) + ',' + height + ')';
                });
            label.append('text')
                .text(function(d) { return d; })
                .style('font-size', '14px')
                .style('font-family', 'sans-serif')
                .style('text-anchor', 'middle');

            // Add the axis ...
            // ... front
            axis.front = canvas.append('g')
                .attr('class', 'axis front');
            axis.front.append('polyline')
                .style('stroke', '#000')
                .style('fill', 'none')
                .attr(
                    'points',
                    options.tickWidth + ',0 ' +
                    '0,0 ' +
                    '0,' + (height - options.axisHeight) + ', ' +
                    options.tickWidth + ',' + (height - options.axisHeight)
                );
            axis.front.append('text')
                .text(data.maximum.front + data.axis_units.front)
                .attr('x', 2 * options.tickWidth)
                .attr('y', 14)
                .style('font-size', '14px')
                .style('font-family', 'sans-serif')
                .style('text-anchor', 'start');

            // ... back
            axis.back = canvas.append('g')
                .attr('class', 'axis back')
                .attr('transform', function(d) {
                    return 'translate(' + (width - options.tickWidth) + ',0)';
                });
            axis.back.append('polyline')
                .style('stroke', '#000')
                .style('fill', 'none')
                .attr(
                    'points',
                    '0,0 '+
                    options.tickWidth + ',0 '+
                    options.tickWidth + ',' + (height - options.axisHeight) + ', ' +
                    '0,' + (height - options.axisHeight)
                );
            axis.back.append('text')
                .text(data.maximum.back + data.axis_units.back)
                .attr('x', -2 * options.tickWidth)
                .attr('y', 14)
                .style('font-size', '14px')
                .style('font-family', 'sans-serif')
                .style('text-anchor', 'end');

            axis.all = d3.selectAll('.axis');

            // Add the bars
            // ... back
            bar.back = canvas.selectAll('.back-bar')
                .data(data.results)
                .enter().append('g')
                .attr('class', 'bar back')
                .attr('transform', function(d) {
                    return 'translate(' + (scale.x(d.group) + scale.dx(d.item)) + ',' + scale.y.back(d.value.back) + ')';
                });
            bar.back.append('rect')
                .attr('width', options.barInnerWidth)
                .attr('height', function(d) {
                    return height - options.axisHeight - scale.y.back(d.value.back) + 1;
                })
                .style('fill', function(d) {
                    return d.active ? '#0571b0' : '#999';
                });

            // ... front
            bar.front = canvas.selectAll('.front-bar')
                .data(data.results)
                .enter().append('g')
                .attr('class', 'bar front')
                .attr('transform', function(d) {
                    return 'translate(' + (scale.x(d.group) + scale.dx(d.item) + 1) + ',' + scale.y.front(d.value.front) + ')';
                });
            bar.front.append('rect')
                .attr('width', options.barInnerWidth - 2)
                .attr('height', function(d) {
                    return height - options.axisHeight - scale.y.front(d.value.front) + 1;
                })
                .attr('fill-opacity', 0.0)
                .attr('stroke', '#000')
                .attr('stroke-width', 2);
            bar.front.each(function(d) {
                if (data.maximum.front / data.groups.length < 5) {
                    var value = 0;
                    for (value = 1; value < d.value.front; ++value) {
                        var y = scale.y.front(value) - scale.y.front(d.value.front);
                        d3.select(this).append('line')
                            .attr('x1', 2)
                            .attr('y1', y)
                            .attr('x2', options.barInnerWidth - 4)
                            .attr('y2', y)
                            .attr('stroke-width', 2)
                            .attr('stroke', '#000');
                    }
                }
            });


            // ... tooltips
            bar.all = d3.selectAll('.bar');
            bar.all.append('title')
                .text(function(d) {
                    return d.group + ' (' + d.item + '): ' +
                        d.value.front + data.axis_units.front + ' / ' +
                        d.value.back  + data.axis_units.back;
                });

            // Add fading effects
            // ... on bars
            bar.all.on('mouseover', function(d) {
                bar.all.filter(function(s) { return !(s.group === d.group && s.item === d.item); })
                    .transition()
                    .duration(700)
            		.style('opacity', 0.1);
            });
            bar.all.on('mouseout', function(d) {
                bar.all.transition()
                    .duration(700)
            		.style('opacity', 1);
            });

            // ... on x axis labels
            label.on('mouseover', function(d) {
                bar.all.filter(function(s) { return s.group !== d; })
                    .transition()
                    .duration(700)
            		.style('opacity', 0.1);
            });
            label.on('mouseout', function(d) {
                bar.all.transition()
                    .duration(700)
            		.style('opacity', 1);
            });

            // ... on y axis
            axis.front.on('mouseover', function(d) {
                bar.back
                    .transition()
                    .duration(700)
            		.style('opacity', 0.1);
            });
            axis.back.on('mouseover', function(d) {
                bar.front
                    .transition()
                    .duration(700)
            		.style('opacity', 0.1);
            });
            axis.all.on('mouseout', function(d) {
                bar.all.transition()
                    .duration(700)
            		.style('opacity', 1);
            });


            // Add download link
            var download_link = $(el).data('download-link');
            if (download_link) {
                append_svg_download_link(el, $(el).html(), data.title, download_link);
            }

            // Add embed link
            var embed_link = $(el).data('embed-link');
            var embed_source = $(el).data('embed-source');
            if (embed_link && embed_source) {
                append_embed_code(el, '100%', 400, embed_source, embed_link);
            }
        }
    });

    d3.select(window).on('resize.groupedbarchart', function() {
        if (bar.all && label) {
            // Resize
            width = $(el).width() - margin.left - margin.right;
            svg.attr('width', width + margin.left + margin.right);
            scale.x.rangeRoundPoints([0, width], 1.0);

            label.attr('transform', function(d) {
                return 'translate(' + scale.x(d) + ',' + height + ')';
            });
            axis.back.attr('transform', function(d) {
                return 'translate(' + (width - options.tickWidth) + ',0)';
            });
            bar.front.attr('transform', function(d) {
                return 'translate(' + (scale.x(d.group) + scale.dx(d.item) + 1) + ',' + scale.y.front(d.value.front) + ')';
            });
            bar.back.attr('transform', function(d) {
                return 'translate(' + (scale.x(d.group) + scale.dx(d.item)) + ',' + scale.y.back(d.value.back) + ')';
            });
        }
    });
};

(function($) {
    $(document).ready(function() {
        $('.grouped-bar-chart').each(function(ix, el) {
            init_bar_chart(el);
        });
    });
})(jQuery);
