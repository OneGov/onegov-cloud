// A bar chart with horizontal bars, optionally a vertical line to indicate
// a majority and hover effects.
//
// Each line consists of the following parts:
//
//      TEXT [========== BAR ====== VALUE / VALUE2 ] VALUE / VALUE2
//           ^- Offset
//
// See https://bost.ocks.org/mike/chart for the reusable charts pattern.
//
var barChart = function(params) {
    var data = {};
    var height = 80;
    var width = 720;
    var interactive = false;

    if (params) {
        if (params.data) data = params.data;
        if (params.interactive) interactive = params.interactive;
        if (params.width) width = params.width;
    }

    var chart = function(container) {

        var svg = d3.select(container).append('svg')
            .attr('xmlns', "http://www.w3.org/2000/svg")
            .attr('version', '1.1');

        if (data.results) {

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

            height = 24 * data.results.length;
            svg.attr('width', width).attr('height', height);

            // Add a container for each line, which contains ...
            var line = svg.selectAll('g')
                .data(data.results)
                .enter().append('g')
                .attr('class', 'line')
                .attr('transform', function(d, i) {return 'translate(0,' + i * 24 + ')';});

            // ... the text to the left
            var name = line.append('text')
                .attr('y', 24 / 2)
                .attr('dy', '4')
                .attr('class', 'name')
                .text(function(d) { return d.text; })
                .style("font-size", "14px")
                .style("font-family", "sans-serif")
                .style("text-anchor", "end");

            // Adjust the offset & scale to give the text enough space
            var offset = d3.max(name[0], function(d) {return d.getBBox().width;});
            var scale = d3.scale.linear()
                .domain([0, d3.max(data.results, function(d) { return d.value; })])
                 .range([0, width - offset]);
            name.attr('x', offset);

            // ... the bar on the right (blue, if active)
            var bar = line.append('rect')
                .attr('x', offset + 5)
                .attr('width', function(d) { return scale(d.value); })
                .attr('height', 24 - 2)
                .attr('class', function(d) {
                    return 'bar ' + d.class;
                })
                .style("fill", "#999");
            bar.filter(function(d) { return d.class == "active"; })
                .style("fill", "#0571b0");

            // ... and the label (one text inside the bar, one outside)
            var label = line.append('g')
                .attr('transform', function(d) {
                  return 'translate(' + (offset + scale(d.value)) + ',16)';
                })
                .attr('class', 'label');
            label.append('text')
                .attr('dx', -3)
                .attr('class', 'left')
                .text(function(d) { return (!d.value2) ? d.value : d.value + ' / ' + (d.value2 || 0); })
                .style("font-size", "12px")
                .style("font-family", "sans-serif")
                .style("text-anchor", "end")
                .style("fill", "#FFF");
            label.append('text')
                .attr('dx', 8)
                .attr('class', 'right')
                .text(function(d) { return (!d.value2) ? d.value : d.value + ' / ' + (d.value2 || 0); })
                .style("font-size", "12px")
                .style("font-family", "sans-serif")
                .style("fill", "#999");

            updateLabels(line);

            // Add a line to indicate the majority
            var majority_line = null;
            if (data.majority) {
                var majority = data.majority;
                majority_line = svg.append("line")
                    .attr("x1", offset + 5 + scale(majority))
                    .attr("x2", offset + 5 + scale(majority))
                    .attr("y1", 0)
                    .attr("y2", 24 * data.results.length)
                    .attr("stroke-width", 3)
                    .attr("stroke", "black")
                    .style("stroke-dasharray", ("4, 4"));
            }

            // Fade-Effect on mouseover
            if (interactive) {
                bar.on("mouseover", function(d) {
                	bar.filter(function(s) { return s != d; })
                        .transition()
                        .duration(700)
                		.style("opacity", 0.1);
                });
                bar.on("mouseout", function(d) {
                    bar.transition()
                        .duration(700)
                		.style("opacity", 1);
                });
            }

            // Relayout on resize
            if (interactive) {

                d3.select(window).on('resize.barchart', function() {
                    if (bar && label) {
                        // Resize
                        width = $(container).width();
                        scale.range([0, width - offset]);

                        svg.attr('width', width);
                        bar.attr('width', function(d) { return scale(d.value); });
                        label.attr('transform', function(d) {
                          return 'translate(' + (offset + scale(d.value)) + ',16)';
                        });
                        updateLabels(line);

                        if (majority_line) {
                            majority_line.attr("x1", offset + 5 + scale(majority));
                            majority_line.attr("x2", offset + 5 + scale(majority));
                        }
                    }
                });
            }
        }
        return chart;
    };

    chart.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return chart;
    };

    chart.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return chart;
    };

    return chart;
};
