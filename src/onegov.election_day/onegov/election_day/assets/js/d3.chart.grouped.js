//
// A bar chart with grouped vertcial bars.
//
(function(root, factory) {
  if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = factory;
  } else {
    root.groupedChart = factory(root.d3);
  }
}(this, function(d3) {
    return function(params) {
        var data = {};
        var margin = {top: 20, right: 10, bottom: 20, left: 10};
        var height = 400 - margin.top - margin.bottom;
        var width = 0;
        var options = {
            axisHeight: 30,
            barOuterWidth: 25,
            barInnerWidth: 22,
            tickWidth: 5,
            fontSize: '14px',
            fontFamily: 'sans-serif',
            colorActive: '#0571b0',
            colorInactive: '#999'
        };
        var interactive = false;

        if (params) {
            if (params.data) data = params.data;
            if (params.margin) margin = params.margin;
            if (params.height) height = params.height - margin.top - margin.bottom;
            if (params.width) width = params.width - margin.left - margin.right;
            if (params.options) options = params.options;
            if (params.interactive) interactive = params.interactive;
        }

        var updateScales = function(scale) {
            // Adjusts the x/dx scales to the current width. If there is not
            // enough space to show all bars, layout all bars of one group
            // to the same position.
            scale.x.rangeRoundPoints([0, width], 1.0);
            scale.simple = (width < data.groups.length * data.labels.length * options.barOuterWidth * 1.2);
            if (scale.simple) {
                scale.dx.range([-Math.round(options.barOuterWidth/2)]);
            } else {
                scale.dx.rangeRoundBands([
                    -(data.labels.length * options.barOuterWidth)/2,
                     (data.labels.length * options.barOuterWidth)/2
                ]);
            }
        };

        var chart = function(container) {

            // Try to read a default width from the container if none is given
            if ((typeof $ !== 'undefined') && !width) {
                width = $(container).width() - margin.left - margin.right;
            }

            var svg = d3.select(container).append('svg')
                .attr('xmlns', "http://www.w3.org/2000/svg")
                .attr('version', '1.1')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .style('shape-rendering', 'crispEdges');

            var canvas = svg.append('g')
                .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

            if (data.results) {

                // Define 4 scales to position the bars:
                // - one to get the x-center of a group
                // - one to get the x-position of the bar in relation to the group
                // - one to get the the y-position of the front bars
                // - one to get the the y-position of the back bars
                var scale = {
                    x: d3.scale.ordinal(),
                    dx: d3.scale.ordinal(),
                    y: {
                        front: d3.scale.linear().rangeRound([height - options.axisHeight, 0]),
                        back: d3.scale.linear().rangeRound([height - options.axisHeight, 0])
                    },
                    simple: false
                };

                var axis = {front: null, back: null, all: null};
                var bar = {front: null, back: null, all: null};
                var label = null;

                if (data.results && data.labels && data.groups && data.maximum && data.axis_units) {

                    // Adjust the scales
                    scale.x.domain(data.groups);
                    scale.dx.domain(data.labels);
                    scale.y.front.domain([0, data.maximum.front]);
                    scale.y.back.domain([0, data.maximum.back]);
                    updateScales(scale);

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
                        .style('font-size', options.fontSize)
                        .style('font-family', options.fontFamily)
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
                            options.tickWidth + ',1 ' +
                            '1,1 ' +
                            '1,' + (height - options.axisHeight) + ', ' +
                            options.tickWidth + ',' + (height - options.axisHeight)
                        );
                    axis.front.append('text')
                        .text(data.maximum.front + data.axis_units.front)
                        .attr('x', 2 * options.tickWidth)
                        .attr('y', options.fontSize)
                        .style('font-size', options.fontSize)
                        .style('font-family', options.fontFamily)
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
                            '1,1 '+
                            options.tickWidth + ',1 '+
                            options.tickWidth + ',' + (height - options.axisHeight) + ', ' +
                            '1,' + (height - options.axisHeight)
                        );
                    axis.back.append('text')
                        .text(data.maximum.back + data.axis_units.back)
                        .attr('x', -2 * options.tickWidth)
                        .attr('y', options.fontSize)
                        .style('font-size', options.fontSize)
                        .style('font-family', options.fontFamily)
                        .style('text-anchor', 'end');

                    axis.all = canvas.selectAll('.axis');

                    // Add the bars
                    // ... back
                    bar.back = canvas.selectAll('.back-bar')
                        .data(data.results)
                        .enter().append('g')
                        .attr('class', 'bar back')
                        .attr('transform', function(d) {
                            return 'translate(' + Math.round(scale.x(d.group) + scale.dx(d.item)) + ',' + scale.y.back(d.value.back) + ')';
                        })
                        .attr('visibility', function(d) {
                            return (scale.simple && !d.active) ? 'hidden' : 'visible';
                        });
                    bar.back.append('rect')
                        .attr('width', options.barInnerWidth)
                        .attr('height', function(d) {
                            return height - options.axisHeight - scale.y.back(d.value.back) + 1;
                        })
                        .style('fill', function(d) {
                            if (d.color) return d.color;
                            return d.active ? options.colorActive : options.colorInactive;
                        })
                        .style('fill-opacity', function(d) {
                            if (d.color && !d.active) return 0.3;
                        });

                    // ... front
                    bar.front = canvas.selectAll('.front-bar')
                        .data(data.results)
                        .enter().append('g')
                        .attr('class', 'bar front')
                        .attr('transform', function(d) {
                            return 'translate(' + Math.round(scale.x(d.group) + scale.dx(d.item)) + ',' + scale.y.front(d.value.front) + ')';
                        })
                        .attr('visibility', function(d) {
                            return (scale.simple && !d.active) ? 'hidden' : 'visible';
                        });
                    bar.front.append('rect')
                        .attr('width', options.barInnerWidth)
                        .attr('height', function(d) {
                            return height - options.axisHeight - scale.y.front(d.value.front) + 1;
                        })
                        .attr('fill-opacity', 0.0)
                        .attr('stroke', '#000')
                        .attr('stroke-dasharray', function(d) {
                            return d.active ? 'initial' : '2 2';
                        })
                        .attr('stroke-width', 1);
                    bar.front.each(function(d) {
                        if (data.maximum.front / data.groups.length < 5) {
                            var value = 0;
                            for (value = 1; value < d.value.front; ++value) {
                                var y = scale.y.front(value) - scale.y.front(d.value.front);
                                d3.select(this).append('line')
                                    .attr('x1', 0)
                                    .attr('y1', y)
                                    .attr('x2', options.barInnerWidth - 1)
                                    .attr('y2', y)
                                    .attr('stroke', '#000')
                                    .attr('stroke-dasharray', function(d) {
                                        return d.active ? 'initial' : '2 2';
                                    })
                                    .attr('stroke-width', 1);
                            }
                        }
                    });


                    // ... tooltips
                    bar.all = canvas.selectAll('.bar');
                    bar.all.append('title')
                        .text(function(d) {
                            return d.group + ' (' + d.item + '): ' +
                                d.value.front + data.axis_units.front + ' / ' +
                                d.value.back  + data.axis_units.back;
                        });

                    // Add fading effects
                    if (interactive) {
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
                    }

                    // Relayout on resize
                    if (interactive) {
                        d3.select(window).on('resize.groupedbarchart', function() {
                            if (bar.all && label) {
                                // Resize
                                width = $(container).width() - margin.left - margin.right;
                                svg.attr('width', width + margin.left + margin.right);
                                updateScales(scale);
                                bar.front.attr('visibility', function(d) {
                                    return (scale.simple && !d.active) ? 'hidden' : 'visible';
                                });
                                bar.back.attr('visibility', function(d) {
                                    return (scale.simple && !d.active) ? 'hidden' : 'visible';
                                });

                                label.attr('transform', function(d) {
                                    return 'translate(' + scale.x(d) + ',' + height + ')';
                                });
                                axis.back.attr('transform', function(d) {
                                    return 'translate(' + (width - options.tickWidth) + ',0)';
                                });
                                bar.front.attr('transform', function(d) {
                                    return 'translate(' + Math.round(scale.x(d.group) + scale.dx(d.item)) + ',' + scale.y.front(d.value.front) + ')';
                                });
                                bar.back.attr('transform', function(d) {
                                    return 'translate(' + Math.round(scale.x(d.group) + scale.dx(d.item)) + ',' + scale.y.back(d.value.back) + ')';
                                });
                            }
                        });
                    }
                }

            }

            return chart;
        };

        chart.width = function() {
            return width + margin.left + margin.right;
        };

        chart.height = function() {
            return height + margin.top + margin.bottom;
        };

        return chart;
    };
}));
