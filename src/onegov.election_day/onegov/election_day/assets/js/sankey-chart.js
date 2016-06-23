var init_sankey_chart = function(el) {

    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var height = 600;
    var svg = d3.select(el).append('svg')
        .attr('width', width)
        .attr('height', height + 15);
    var sankey = d3.sankey()
        .nodeWidth(20)
        .nodePadding(15)
        .size([width, height]);

    var path = sankey.link();

    $.ajax({ url: dataurl }).done(function(data) {

        sankey.nodes(data.nodes)
            .links(data.links)
            .layout(1);

        var link = svg.append("g").selectAll(".link")
            .data(data.links)
            .enter().append("path")
            .attr("class", "link")
            .attr("d", path)
            .style("stroke-width", function(d) { return Math.max(1, d.dy); })
            .sort(function(a, b) { return b.dy - a.dy; });

        link.append("title")
            .text(function(d) { return d.value; });

        var node = svg.append("g").selectAll(".node")
            .data(data.nodes)
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
            .call(
                d3.behavior.drag()
                    .origin(function(d) { return d; })
                    .on("dragstart", function() { this.parentNode.appendChild(this); })
                    .on("drag", dragmove)
            );

        node.append("rect")
            .attr("height", function(d) { return d.dy; })
            .attr("width", sankey.nodeWidth())
            .attr("class", function(d) { return d.class; })
            .append("title")
            .text(function(d) { return d.value_2; });

        node.append("text")
            .attr("x", -6)
            .attr("y", function(d) { return d.dy / 2; })
            .attr("dy", ".35em")
            .attr("text-anchor", "end")
            .attr("transform", null)
            .text(function(d) { return d.name; })
            .filter(function(d) { return d.x < width / 2; })
            .attr("x", 6 + sankey.nodeWidth())
            .attr("text-anchor", "start");

      function dragmove(d) {
        d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
        sankey.relayout();
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
