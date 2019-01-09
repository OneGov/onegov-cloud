//
// A bar chart with horizontal yea/nay bars.
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
            colorYea: '#457439',
            colorNay: '#a4112e', // == logo color
            colorOpacity: 0.7
        };

        if (params) {
            if ('data' in params) data = params.data;
            if ('margin' in params) margin = params.margin;
            if ('interactive' in params) interactive = params.interactive;
            if ('width' in params) width = params.width;
            if ('options' in params) options = params.options;
        }

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
                    .clamp(true)
                    .domain([0, 100])
                    .range([0, width - offset - 8]);
                name.attr('x', offset);

                // ... the bars on the right
                var bar_yea = line.append('rect')
                    .attr('x', offset + 5)
                    .attr('width', function(d) { return scale(d.value); })
                    .attr('height', options.barHeight - options.barMargin)
                    .attr('class', 'bar yea')
                    .style('fill', options.colorYea)
                    .style('opacity', options.colorOpacity);
                bar_yea.append('title')
                    .text(function(d) { return d.value + '%'; });

                var bar_nay = line.append('rect')
                    .attr('x', function(d) { return offset + 5 + scale(d.value); })
                    .attr('width', function(d) { return scale(100 - d.value); })
                    .attr('height', options.barHeight - options.barMargin)
                    .attr('class', 'bar nay')
                    .style('fill', options.colorNay)
                    .style('opacity', options.colorOpacity);
                bar_nay.append('title')
                    .text(function(d) { return (Math.round(10 * (100 - d.value)) / 10) + '%'; });

                var bar = canvas.selectAll('rect.bar');

                // Add a 50% line
                var middle_line = canvas.append('line')
                    .attr('x1', offset + 5 + scale(50))
                    .attr('x2', offset + 5 + scale(50))
                    .attr('y1', 0)
                    .attr('y2', options.barHeight * data.results.length)
                    .attr('stroke-width', 1)
                    .attr('stroke', 'white')
                    .style('stroke-dasharray', ('4, 4'));

                // Fade-Effect on mouseover
                if (interactive) {
                    bar_yea.on('mouseover', function(d) {
                        bar_yea.filter(function(s) { return s != d; })
                            .transition()
                            .duration(700)
                    		    .style('opacity', 0.1);
                        bar_nay.transition()
                            .duration(700)
                    		    .style('opacity', 0.1);
                    });
                    bar_nay.on('mouseover', function(d) {
                        bar_nay.filter(function(s) { return s != d; })
                            .transition()
                            .duration(700)
                    		    .style('opacity', 0.1);
                        bar_yea.transition()
                            .duration(700)
                            .style('opacity', 0.1);
                    });
                    bar.on('mouseout', function(d) {
                        bar.transition()
                            .duration(700)
                    		    .style('opacity', options.colorOpacity);
                    });
                }

                // Relayout on resize
                if (interactive) {

                    d3.select(window).on('resize.barchart', function() {
                        if (bar) {
                            // Resize
                            width = ($(container).width() - margin.left - margin.right);
                            scale.range([0, width - offset - 8]);

                            svg.attr('width', width + margin.left + margin.right);
                            bar_yea.attr('width', function(d) { return scale(d.value); });
                            bar_nay.attr('x', function(d) { return offset + 5 + scale(d.value); });
                            bar_nay.attr('width', function(d) { return scale(100 - d.value); });
                            middle_line.attr('x1', offset + 5 + scale(50));
                            middle_line.attr('x2', offset + 5 + scale(50));
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
