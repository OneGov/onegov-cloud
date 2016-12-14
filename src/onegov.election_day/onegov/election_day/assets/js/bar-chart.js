var update_labels = function(line) {
    line.each(function() {
        var box_width = this.childNodes[1].getBBox().width;
        var label_left =this.childNodes[2].childNodes[0];
        var label_right =this.childNodes[2].childNodes[1];
        if ((box_width-10) < label_left.getBBox().width) {
            label_left.setAttribute('visibility', 'hidden');
            label_right.setAttribute('visibility', 'visible');
        } else {
            label_left.setAttribute('visibility', 'visible');
            label_right.setAttribute('visibility', 'hidden');
        }
    });
};

var label_text = function(d) {
    if (!d.value2) {
        return d.value;
    }
    return d.value + ' / ' + (d.value2 || 0);
};

var init_bar_chart = function(el) {

    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var svg = d3.select(el).append('svg')
        .attr('width', width)
        .attr('xmlns', "http://www.w3.org/2000/svg")
        .attr('version', '1.1');
    var offset = width * 0.25;
    var scale = d3.scale.linear();
    var line = null;
    var bar = null;
    var label = null;
    var majority = null;
    var majority_line = null;

    $.ajax({ url: dataurl }).done(function(data) {

        if (data.results) {

            svg.attr('height', 24 * data.results.length);

            line = svg.selectAll('g')
                .data(data.results)
                .enter().append('g')
                .attr('class', 'line')
                .attr('transform', function(d, i) {
                  return 'translate(0,' + i * 24 + ')';
                });

            var name = line.append('text')
                .attr('y', 24 / 2)
                .attr('dy', '4')
                .attr('class', 'name')
                .text(function(d) { return d.text; })
                .style("font-size", "14px")
                .style("font-family", "sans-serif")
                .style("text-anchor", "end");

            offset = d3.max(name[0], function(d) {
                return d.getBBox().width;
            });

            name.attr('x', offset);

            scale.domain([0, d3.max(data.results, function(d) { return d.value; })])
                 .range([0, width - offset]);

            bar = line.append('rect')
                .attr('x', offset + 5)
                .attr('width', function(d) { return scale(d.value); })
                .attr('height', 24 - 2)
                .attr('class', function(d) {
                    return 'bar ' + d.class;
                })
                .style("fill", "#999");

            bar.filter(function(d) { return d.class == "active"; })
                .style("fill", "#0571b0");

            label = line.append('g')
                .attr('transform', function(d) {
                  return 'translate(' + (offset + scale(d.value)) + ',16)';
                })
                .attr('class', 'label');

            label.append('text')
                .attr('dx', -3)
                .attr('class', 'left')
                .text(function(d) { return label_text(d); })
                .style("font-size", "12px")
                .style("font-family", "sans-serif")
                .style("text-anchor", "end")
                .style("fill", "#FFF");
            label.append('text')
                .attr('dx', 8)
                .attr('class', 'right')
                .text(function(d) { return label_text(d); })
                .style("font-size", "12px")
                .style("font-family", "sans-serif")
                .style("fill", "#999");

            update_labels(line);

            if (data.majority) {
                majority = data.majority;
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

            var download_link = $(el).data('download-link');
            if (download_link) {
                append_svg_download_link(el, $(el).html(), data.title, download_link);
            }

            var embed_link = $(el).data('embed-link');
            var embed_source = $(el).data('embed-source');
            if (embed_link && embed_source) {
                append_embed_code(el, '100%', 24 * data.results.length + 50, embed_source, embed_link);
            }
        }
    });

    d3.select(window).on('resize.barchart', function() {
        if (bar && label) {
            // Resize
            width = $(el).width();
            scale.range([0, width - offset]);

            svg.attr('width', width);
            bar.attr('width', function(d) { return scale(d.value); });
            label.attr('transform', function(d) {
              return 'translate(' + (offset + scale(d.value)) + ',16)';
            });
            update_labels(line);

            if (majority_line) {
                majority_line.attr("x1", offset + 5 + scale(majority));
                majority_line.attr("x2", offset + 5 + scale(majority));
            }
        }
    });
};

(function($) {
    $(document).ready(function() {
        $('.bar-chart').each(function(ix, el) {
            init_bar_chart(el);
        });
    });
})(jQuery);
