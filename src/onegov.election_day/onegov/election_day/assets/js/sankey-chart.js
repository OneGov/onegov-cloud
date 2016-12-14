var adjust_scale = function(scale, width, offset, nodeWidth, inverse) {
    scale.range([
        offset.left + offset.margin,
        width - offset.right - offset.margin - nodeWidth
    ]);
    if (inverse) {
        scale.range([
            width - offset.left - offset.margin - nodeWidth,
            offset.right + offset.margin
        ]);
    }
};

var init_sankey_chart = function(el) {

    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var height = 600;
    var svg = d3.select(el).append('svg')
        .attr('width', width)
        .attr('height', height + 40)
        .attr('xmlns', "http://www.w3.org/2000/svg")
        .attr('version', '1.1')
        .style('padding-top', '20px');
    var offset = {left: 0, right: 0, margin: 6};
    var scale = d3.scale.linear().domain([0, width]);
    var nodeWidth = 25;
    var sankey = d3.sankey()
        .nodeWidth(nodeWidth)
        .nodePadding(15)
        .size([width, height]);
    var node = null;
    var link = null;
    var path = null;
    var inverse = $(el).data('inverse') || false;

    $.ajax({ url: dataurl }).done(function(data) {

        if (data.nodes && data.links) {

            sankey.nodes(data.nodes)
                .links(data.links)
                .layout(1);

            // Add the nodes <g><rect><text></g>
            var count = 0;
            node = svg.append("g").selectAll(".node")
                .data(data.nodes)
                .enter().append("g")
                .attr("class", "node")
                .attr("id", function(d) { return 'node-' + count++; })
                .call(
                    d3.behavior.drag()
                        .origin(function(d) { return d; })
                        .on("dragstart", function() { this.parentNode.appendChild(this); })
                        .on("drag", function(d) {
                            d3.select(this).attr("transform", "translate(" + scale(d.x) + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
                            sankey.relayout();
                            link.attr("d", path);
                        })
                );

            // ... the bar
            var bar = node.append("rect")
                .attr("height", function(d) { return d.dy; })
                .attr("width", nodeWidth)
                .style("cursor", "move")
                .style("fill", "#999")
                .style("shape-rendering", "crispEdges");
            bar.append("title")
                .text(function(d) { return d.value; });
            bar.filter(function(d) { return d.active; })
                .style("fill", "#0571b0");

            // ... the inner value of the bar
            node.filter(function(d) { return d.display_value; })
                .append("text")
                .text(function(d) { return d.display_value; })
                .attr("x", 0)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dx", ".5em")
                .attr("dy", ".35em")
                .style("font-size", "14px")
                .style("font-family", "sans-serif")
                .style("fill", "#fff")
                .style("pointer-events", "none");

            // Add the node names to the left and right of the bars
            var name = node.filter(function(d) { return d.name; })
                .append("text")
                .text(function(d) { return d.name; })
                .attr("x", 0)
                .attr("y", function(d) { return d.dy / 2; })
                .attr("dy", ".35em")
                .attr("class", "left")
                .style("pointer-events", "none")
                .style("font-size", "14px")
                .style("font-family", "sans-serif");
            var name_left = name.filter(function(d) { return d.x < width / 2;})
                .attr("class", "name name-left")
                .attr("text-anchor", "end")
                .attr("dx", -offset.margin);
            var name_right = name.filter(function(d) { return d.x > width / 2;})
                .attr("class", "name name-right")
                .attr("text-anchor", "start")
                .attr("dx", nodeWidth + offset.margin);
            if (inverse) {
                name_left.attr("text-anchor", "start")
                    .attr("dx", nodeWidth + offset.margin);
                name_right.attr("text-anchor", "end")
                    .attr("dx", -offset.margin);
            }

            // Rescale the sankey diagram to leave place to the left and right
            // for the node names
            //
            // NAME | <-- offset.margin --> SANKEY <-- offset.margin --> | NAME
            //      ^- offset.left                         offset.right -^
            //
            offset.left = d3.max(name_left[0], function(d) { return d.getBBox().width;}) || 0;
            offset.right = d3.max(name_right[0], function(d) { return d.getBBox().width;}) || 0;
            adjust_scale(scale, width, offset, nodeWidth, inverse);

            node.attr("transform", function(d) { return "translate(" + scale(d.x) + "," + d.y + ")"; });

            // Add the links
            path = sankey.link(
                scale,
                inverse ? -nodeWidth : 0,
                inverse ? nodeWidth : 0
            );
            link = svg.append("g").selectAll(".link")
                .data(data.links)
                .enter().append("path")
                .attr("class", "link")
                .attr("d", path)
                .attr("style", function(d) { return "stroke: #000; stroke-opacity: 0.2; fill: none; stroke-width: " + Math.round(Math.max(1, d.dy)) + "px"; })
                .sort(function(a, b) { return b.dy - a.dy; });

            link.append("title")
                .text(function(d) { return d.value; });

            // Fade-Effect on mouseover
            node.on("mouseover", function(d) {
            	link.transition()
                    .duration(700)
            		.style("opacity", 0.1);
            	link.filter(function(s) { return d.id == s.source.id; })
                    .transition()
                    .duration(700)
            		.style("opacity", 1);
            	link.filter(function(t) { return d.id == t.target.id; })
                    .transition()
                    .duration(700)
            		.style("opacity", 1);
            });
            node.on("mouseout", function(d) {
                link.transition()
                    .duration(700)
            		.style("opacity", 1);
            });
            link.on("mouseover", function(d) {
            	link.filter(function(s) { return s != d; })
                    .transition()
                    .duration(700)
            		.style("opacity", 0.1);
            });
            link.on("mouseout", function(d) {
                link.transition()
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
                append_embed_code(el, '100%', height + 50, embed_source, embed_link);
            }
        }
    });

    d3.select(window).on('resize.sankey', function() {
        if (node && link && path) {
            // Resize
            width = $(el).width();
            svg.attr('width', width);

            adjust_scale(scale, width, offset, nodeWidth, inverse);
            node.attr("transform", function(d) { return "translate(" + scale(d.x) + "," + d.y + ")"; });
            path = sankey.link(
                scale,
                inverse ? -nodeWidth : 0,
                inverse ? nodeWidth : 0
            );
            link.attr("d", path);
        }
    });
};

(function($) {
    $(document).ready(function() {
        $('.sankey-chart').each(function(ix, el) {
            init_sankey_chart(el);
        });
    });
})(jQuery);
