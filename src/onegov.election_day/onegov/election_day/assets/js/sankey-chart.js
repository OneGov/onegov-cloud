var init_sankey_chart = function(el) {

    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var svg = d3.select(el).append('svg').attr('width', width).attr('height', 1500);

    // var margin = {top: 1, right: 1, bottom: 6, left: 1},
    //     width = 960 - margin.left - margin.right,
    //     height = 500 - margin.top - margin.bottom;
    //
    var height = 500;
    var formatNumber = d3.format(",.0f");
    var format = function(d) { return formatNumber(d) + " TWh"; };
    var color = d3.scale.category20();

    // var svg = d3.select("#chart").append("svg")
    //     .attr("width", width + margin.left + margin.right)
    //     .attr("height", height + margin.top + margin.bottom)
    //   .append("g")
    //     .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    //
    var sankey = d3.sankey()
        .nodeWidth(15)
        .nodePadding(10)
        .size([width, height]);

    var path = sankey.link();

    $.ajax({ url: dataurl }).done(function(data) {

        // sankey.nodes([]).links([]).layout(32);
        sankey.nodes(data.nodes)
            .links(data.links)
            .layout(32);

      var link = svg.append("g").selectAll(".link")
          .data(data.links)
        .enter().append("path")
          .attr("class", "link")
          .attr("d", path)
          .style("stroke-width", function(d) { return Math.max(1, d.dy); })
          .sort(function(a, b) { return b.dy - a.dy; });

      link.append("title")
          .text(function(d) { return d.source.name + " → " + d.target.name + "\n" + format(d.value); });

      var node = svg.append("g").selectAll(".node")
          .data(data.nodes)
        .enter().append("g")
          .attr("class", "node")
          .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
        .call(d3.behavior.drag()
          .origin(function(d) { return d; })
          .on("dragstart", function() { this.parentNode.appendChild(this); })
          .on("drag", dragmove));

      node.append("rect")
          .attr("height", function(d) { return d.dy; })
          .attr("width", sankey.nodeWidth())
          .style("fill", function(d) { return d.color = color(d.name.replace(/ .*/, "")); })
          .style("stroke", function(d) { return d3.rgb(d.color).darker(2); })
        .append("title")
          .text(function(d) { return d.name + "\n" + format(d.value); });

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
    })

    // $.ajax({ url: dataurl }).done(function(data) {

        // svg.attr('height', 24 * data.results.length);
        //
        // line = svg.selectAll('g')
        //     .data(data.results)
        //     .enter().append('g')
        //     .attr('class', 'line')
        //     .attr('transform', function(d, i) {
        //       return 'translate(0,' + i * 24 + ')';
        //     });
        //
        // var name = line.append('text')
        //     .attr('y', 24 / 2)
        //     .attr('dy', '4')
        //     .attr('class', 'name')
        //     .text(function(d) { return d.text; });
        //
        // offset = d3.max(name[0], function(d) {
        //     return d.getBBox().width;
        // });
        //
        // name.attr('x', offset);
        //
        // scale.domain([0, d3.max(data.results, function(d) { return d.value; })])
        //      .range([0, width - offset]);
        //
        // bar = line.append('rect')
        //     .attr('x', offset + 5)
        //     .attr('width', function(d) { return scale(d.value); })
        //     .attr('height', 24 - 2)
        //     .attr('class', function(d) {
        //         return 'bar ' + d.class;
        //     });
        //
        // label = line.append('g')
        //     .attr('transform', function(d) {
        //       return 'translate(' + (offset + scale(d.value)) + ',16)';
        //     })
        //     .attr('class', 'label');
        //
        // label.append('text')
        //     .attr('dx', -3)
        //     .attr('class', 'left')
        //     .text(function(d) { return d.value; });
        // label.append('text')
        //     .attr('dx', 8)
        //     .attr('class', 'right')
        //     .text(function(d) { return d.value; });
        //
        // update_labels(line);
        //
        // if (data.majority) {
        //     majority = data.majority;
        //     majority_line = svg.append("line")
        //         .attr("x1", offset + 5 + scale(majority))
        //         .attr("x2", offset + 5 + scale(majority))
        //         .attr("y1", 0)
        //         .attr("y2", 24 * data.results.length)
        //         .attr("stroke-width", 3)
        //         .attr("stroke", "black")
        //         .style("stroke-dasharray", ("4, 4"));
        // }

    // });

    // d3.select(window).on('resize', function() {
    //     if (bar && label) {
    //         // Resize
    //         width = $(el).width();
    //         scale.range([0, width - offset]);
    //
    //         svg.attr('width', width);
    //         bar.attr('width', function(d) { return scale(d.value); });
    //         label.attr('transform', function(d) {
    //           return 'translate(' + (offset + scale(d.value)) + ',16)';
    //         });
    //         update_labels(line);
    //
    //         if (majority_line) {
    //             majority_line.attr("x1", offset + 5 + scale(majority));
    //             majority_line.attr("x2", offset + 5 + scale(majority));
    //         }
    //     }
    // });
};

(function($) {
    $(document).ready(function() {
        $('.sankey-chart').each(function(ix, el) {
            init_sankey_chart(el);
        });
    });
})(jQuery);
