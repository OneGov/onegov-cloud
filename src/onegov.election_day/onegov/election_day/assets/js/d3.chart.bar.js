//
// A bar chart with horizontal bars, optionally a vertical line to indicate
// a majority and hover effects.
//
(function(root, factory) {
  if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = factory;
  } else {
    root.barChart = factory(root.d3);
  }
}(this, function(d3) {
    return function(params) {
        var data = {};
        var margin = {top: 20, right: 10, bottom: 20, left: 10};
        var height = 0;
        var width = 0;
        var interactive = false;
        var options = {
            barHeight: 24,
            barMargin: 2,
            fontSize: '14px',
            fontSizeSmall: '12px',
            fontFamily: 'sans-serif',
            colorActive: '#0571b0',
            colorInactive: '#999'
        };

        if (params) {
            if (params.data) data = params.data;
            if (params.margin) margin = params.margin;
            if (params.interactive) interactive = params.interactive;
            if (params.width) width = params.width;
            if (params.options) options = params.options;
        }

        var updateLabels = function(line) {
            line.each(function() {
                var box_width = this.childNodes[1].getBBox().width;
                var label_left = this.childNodes[2].childNodes[0];
                var label_right = this.childNodes[2].childNodes[1];
                if ((box_width-10) < label_left.getBBox().width) {
                    label_left.setAttribute('visibility', 'hidden');
                    label_right.setAttribute('visibility', 'visible');
                } else {
                    label_left.setAttribute('visibility', 'visible');
                    label_right.setAttribute('visibility', 'hidden');
                }
            });
        };

        var chart = function(container) {

            var svg = d3.select(container).append('svg')
                .attr('xmlns', 'http://www.w3.org/2000/svg')
                .attr('version', '1.1');

            // Try to read a default width from the container if none is given
            if ((typeof $ !== 'undefined') && !width) {
                width = $(container).width() - margin.left - margin.right;
            }

            if (data.results) {

                height = options.barHeight * data.results.length;

                svg.attr('width', width + margin.left + margin.right)
                    .attr('height', height + margin.top + margin.bottom);

                var canvas = svg.append('g')
                    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

                // Add a container for each line, which contains ...
                var line = canvas.selectAll('g')
                    .data(data.results)
                    .enter().append('g')
                    .attr('class', 'line')
                    .attr('transform', function(d, i) {return 'translate(0,' + i * options.barHeight + ')';});

                // ... the text to the left
                var name = line.append('text')
                    .attr('y', (options.barHeight - options.barMargin) / 2)
                    .attr('dy', '4')
                    .attr('class', 'name')
                    .text(function(d) { return d.text; })
                    .style('font-size', options.fontSize)
                    .style('font-family', options.fontFamily)
                    .style('text-anchor', 'end');

                // Adjust the offset & scale to give the text enough space
                var offset = d3.max(name[0], function(d) {return d.getBBox().width;});
                var scale = d3.scale.linear()
                    .domain([0, Math.max(data.majority || 0, d3.max(data.results, function(d) { return d.value; }))])
                    .range([0, width - offset - 8]);
                name.attr('x', offset);

                // ... the bar on the right (blue, if active)
                var bar = line.append('rect')
                    .attr('x', offset + 5)
                    .attr('width', function(d) { return scale(d.value); })
                    .attr('height', options.barHeight - options.barMargin)
                    .attr('class', function(d) {
                        return 'bar ' + d.class;
                    })
                    .style('fill', options.colorInactive);
                bar.filter(function(d) { return d.class == 'active'; })
                    .style('fill', options.colorActive);

                // ... and the label (one text inside the bar, one outside)
                var label = line.append('g')
                    .attr('transform', function(d) {
                      return 'translate(' + (offset + scale(d.value)) + ',' + ((options.barHeight - options.barMargin) / 2 + 4) + ')';
                    })
                    .attr('class', 'label');
                label.append('text')
                    .attr('dx', -3)
                    .attr('class', 'left')
                    .text(function(d) { return (!d.value2) ? d.value : d.value + ' / ' + (d.value2 || 0); })
                    .style('font-size', options.fontSizeSmall)
                    .style('font-family', options.fontFamily)
                    .style('text-anchor', 'end')
                    .style('fill', '#FFF');
                label.append('text')
                    .attr('dx', 8)
                    .attr('class', 'right')
                    .text(function(d) { return (!d.value2) ? d.value : d.value + ' / ' + (d.value2 || 0); })
                    .style('font-size', options.fontSizeSmall)
                    .style('font-family', options.fontFamily)
                    .style('fill', options.colorInactive);

                updateLabels(line);

                // Add a line to indicate the majority
                var majority_line = null;
                if (data.majority) {
                    var majority = data.majority;
                    majority_line = canvas.append('line')
                        .attr('x1', offset + 5 + scale(majority))
                        .attr('x2', offset + 5 + scale(majority))
                        .attr('y1', 0)
                        .attr('y2', options.barHeight * data.results.length)
                        .attr('stroke-width', 3)
                        .attr('stroke', 'black')
                        .style('stroke-dasharray', ('4, 4'));
                }

                // Fade-Effect on mouseover
                if (interactive) {
                    bar.on('mouseover', function(d) {
                        bar.filter(function(s) { return s != d; })
                            .transition()
                            .duration(700)
                    		    .style('opacity', 0.1);
                        label.filter(function(s) { return s != d; })
                            .transition()
                            .duration(700)
                    		    .style('opacity', 0.1);
                    });
                    bar.on('mouseout', function(d) {
                        bar.transition()
                            .duration(700)
                    		    .style('opacity', 1);
                        label.transition()
                            .duration(700)
                    		    .style('opacity', 1);
                    });
                }

                // Relayout on resize
                if (interactive) {

                    d3.select(window).on('resize.barchart', function() {
                        if (bar && label) {
                            // Resize
                            width = ($(container).width() - margin.left - margin.right);
                            scale.range([0, width - offset - 8]);

                            svg.attr('width', width + margin.left + margin.right);
                            bar.attr('width', function(d) { return scale(d.value); });
                            label.attr('transform', function(d) {
                              return 'translate(' + (offset + scale(d.value)) + ',' + ((options.barHeight - options.barMargin) / 2 + 4) + ')';
                            });
                            updateLabels(line);

                            if (majority_line) {
                                majority_line.attr('x1', offset + 5 + scale(majority));
                                majority_line.attr('x2', offset + 5 + scale(majority));
                            }
                        }
                    });
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
