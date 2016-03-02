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

var init_bar_chart = function(el) {

    var dataurl = $(el).data('dataurl');
    var width = $(el).width();
    var svg = d3.select(el).append('svg').attr('width', width);
    var offset = width * 0.25;
    var scale = d3.scale.linear();
    var line = null;
    var bar = null;
    var label = null;

    $.ajax({ url: dataurl }).done(function(data) {

        svg.attr('height', 24 * data.length);

        line = svg.selectAll('g')
            .data(data)
            .enter().append('g')
            .attr('class', 'line')
            .attr('transform', function(d, i) {
              return 'translate(0,' + i * 24 + ')';
            });

        var name = line.append('text')
            .attr('y', 24 / 2)
            .attr('dy', '4')
            .attr('class', 'name')
            .text(function(d) { return d.text; });

        offset = d3.max(name[0], function(d) {
            return d.getBBox().width;
        });

        name.attr('x', offset);

        scale.domain([0, d3.max(data, function(d) { return d.value; })])
             .range([0, width - offset]);

        bar = line.append('rect')
            .attr('x', offset + 5)
            .attr('width', function(d) { return scale(d.value); })
            .attr('height', 24 - 2)
            .attr('class', function(d) {
                return 'bar ' + d.class;
            });

        label = line.append('g')
            .attr('transform', function(d) {
              return 'translate(' + (offset + scale(d.value)) + ',16)';
            })
            .attr('class', 'label');

        label.append('text')
            .attr('dx', -3)
            .attr('class', 'left')
            .text(function(d) { return d.value; });
        label.append('text')
            .attr('dx', 8)
            .attr('class', 'right')
            .text(function(d) { return d.value; });

        update_labels(line);
    });

    d3.select(window).on('resize', function() {
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
