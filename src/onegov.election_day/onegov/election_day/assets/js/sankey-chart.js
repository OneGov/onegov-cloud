var init_sankey_chart = function(el) {

    var offsetMargin = 6;
    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var height = 600;
    var svg = d3.select(el).append('svg')
        .attr('width', width)
        .attr('height', height + 15)
        .attr('xmlns', "http://www.w3.org/2000/svg")
        .attr('version', '1.1');
    var offset = width * 0.25;
    var scale = d3.scale.linear();
    var sankey = d3.sankey()
        .nodeWidth(25)
        .nodePadding(15)
        .size([width, height]);
    var node = null;
    var link = null;
    var path = null;

    $.ajax({ url: dataurl }).done(function(data) {

        sankey.nodes(data.nodes)
            .links(data.links)
            .layout(1);

        node = svg.append("g").selectAll(".node")
            .data(data.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(
                d3.behavior.drag()
                    .origin(function(d) { return d; })
                    .on("dragstart", function() { this.parentNode.appendChild(this); })
                    .on("drag", dragmove)
            );

        var bar = node.append("rect")
            .attr("height", function(d) { return d.dy; })
            .attr("width", sankey.nodeWidth())
            .style("cursor", "move")
            .style("fill", "#999")
            .style("shape-rendering", "crispEdges")
            .filter(function(d) { return d.value_2 > 0; })
            .style("fill", "#0571b0");
        bar.append("title")
            .text(function(d) { return d.value_2; });

        node.filter(function(d) { return d.value_2 > 0; })
            .append("text")
            .text(function(d) { return d.value_2; })
            .attr("x", 0)
            .attr("y", function(d) { return d.dy / 2; })
            .attr("dx", ".5em")
            .attr("dy", ".35em")
            .style("font-size", "14px")
            .style("font-family", "sans-serif")
            .style("fill", "#fff")
            .style("pointer-events", "none");

        var name = node.filter(function(d) { return d.name; })
            .append("text")
            .text(function(d) { return d.name; })
            .attr("x", 0)
            .attr("y", function(d) { return d.dy / 2; })
            .attr("dx", -offsetMargin)
            .attr("dy", ".35em")
            .attr("text-anchor", "end")
            .style("font-size", "14px")
            .style("font-family", "sans-serif")
            .style("pointer-events", "none");

        offset = d3.max(name[0], function(d) {return d.getBBox().width;});
        scale.domain([0, width]).range([offset+offsetMargin, width-2*offsetMargin]);

        node.attr("transform", function(d) { return "translate(" + scale(d.x) + "," + d.y + ")"; });

        path = sankey.link(scale);
        link = svg.append("g").selectAll(".link")
            .data(data.links)
            .enter().append("path")
            .attr("class", "link")
            .attr("d", path)
            .attr("style", function(d) { return "stroke: #000; stroke-opacity: 0.2; fill: none; stroke-width: " + Math.round(Math.max(1, d.dy)) + "px"; })
            .sort(function(a, b) { return b.dy - a.dy; });

        link.append("title")
            .text(function(d) { return d.value; });

        function dragmove(d) {
            d3.select(this).attr("transform", "translate(" + scale(d.x) + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
            sankey.relayout();
            link.attr("d", path);
        }

        var download_link = $(el).data('download-link');
        if (download_link) {
            append_svg_download_link(el, $(el).html(), data.title, download_link);
        }

        var embed_link = $(el).data('embed-link');
        var embed_source = $(el).data('embed-source');
        if (embed_link && embed_source) {
            append_embed_code(el, '100%', height + 50, embed_source, embed_link);
        }

        if ($(el).is('.foldable.folded .foldable-svg-panel .sankey-chart')) {
            $(el).closest('.foldable-svg-panel').each(function() {
                $(this).hide();
            });
        }
    });

    d3.select(window).on('resize.sankey', function() {
        if (node && link && path) {
            // Resize
            width = $(el).width();
            scale.range([offset+offsetMargin, width-2*offsetMargin]);

            svg.attr('width', width);
            node.attr("transform", function(d) { return "translate(" + scale(d.x) + "," + d.y + ")"; });
            path = sankey.link(scale);
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
