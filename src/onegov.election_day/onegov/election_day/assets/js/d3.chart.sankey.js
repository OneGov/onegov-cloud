//
// A bar chart with horizontal bars, optionally a vertical line to indicate
// a majority and hover effects.
//
(function(root, factory) {
  if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = factory;
  } else {
    root.sankeyChart = factory(root.d3);
  }
}(this, function(d3) {
    return function(params) {
        var data = {};
        var margin = {top: 20, right: 10, bottom: 20, left: 10};
        var height = 720 - margin.top - margin.bottom;
        var width = 0;
        var interactive = false;
        var inverse = false;
        var options = {
            nodeWidth: 25,
            nodePadding: 15,
            fontSize: '14px',
            fontFamily: 'sans-serif',
            colorActive: '#0571b0',
            colorInactive: '#999'
        };

        if (params) {
            if (params.data) data = params.data;
            if (params.margin) margin = params.margin;
            if (params.height) height = params.height;
            if (params.width) width = params.width;
            if (params.interactive) interactive = params.interactive;
            if (params.inverse) inverse = params.inverse;
            if (params.options) options = params.options;
        }

        // We need some more margins to display the (vertically centered)
        // node names
        margin.top += 0.5 * parseInt(options.fontSize);
        margin.bottom += 0.5 * parseInt(options.fontSize);

        var ellipseText = function(text, maximum) {
            // Ellipse the text with '...' if its longer than the given maximum
            text.each(function(d) {
                var self = d3.select(this);
                var text = d.name;
                self.text(text);
                var textLength = this.getComputedTextLength();
                while (textLength > maximum && (text.length > 0)) {
                    text = text.slice(0, -1);
                    self.text(text + '...');
                    textLength = this.getComputedTextLength();
                }
            });
        };

        var adjustOffset = function(name, offset, width) {
            // Calculate the text widths (offsets) and limit them to a maximum
            if (!offset.initial) {
                // Compute and store the full text widths once
                offset.left = d3.max(name.left[0], function(d) { return d.getBBox().width;}) || 0;
                offset.right = d3.max(name.right[0], function(d) { return d.getBBox().width;}) || 0;
                offset.initial = {};
                offset.initial.left = offset.left;
                offset.initial.right = offset.right;
            }
            offset.left = offset.initial.left;
            offset.right = offset.initial.right;
            var maximum = Math.round(width / (2 + (offset.left ? 1 : 0) + (offset.right ? 1 : 0)));
            if (offset.left > maximum) {
                offset.left = maximum;
            }
            if (offset.right > maximum) {
                offset.right = maximum;
            }
            ellipseText(name.left, offset.left);
            ellipseText(name.right, offset.right);
        };

        var adjustScale = function(scale, width, offset, inverse) {
            // Adjusts the scale to fit the sankey diagram within the new limits
            // (width - offsets - margins)
            scale.range([
                offset.left + offset.margin,
                width - offset.right - offset.margin - options.nodeWidth
            ]);
            if (inverse) {
                scale.range([
                    width - offset.left - offset.margin - options.nodeWidth,
                    offset.right + offset.margin
                ]);
            }
        };

        var chart = function(container) {

            // Try to read a default width from the container if none is given
            if ((typeof $ !== 'undefined') && !width) {
                width = $(container).width() - margin.left - margin.right;
            }

            var svg = d3.select(container).append('svg')
                .attr('xmlns', 'http://www.w3.org/2000/svg')
                .attr('version', '1.1')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom);

            if (data.nodes && data.links) {

                var canvas = svg.append('g')
                    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

                var offset = {left: 0, right: 0, margin: 6};
                var name = {};
                var scale = d3.scale.linear().domain([0, width]);

                var sankey = d3.sankey()
                    .nodeWidth(options.nodeWidth)
                    .nodePadding(options.nodePadding)
                    .size([width, height])
                    .nodes(data.nodes)
                    .links(data.links)
                    .layout(1);

                // Add the nodes <g><rect><text></g>
                var count = 0;
                var node = canvas.append('g').selectAll('.node')
                    .data(data.nodes)
                    .enter().append('g')
                    .attr('class', 'node')
                    .attr('id', function(d) { return 'node-' + count++; })
                    .filter(function(d) { return d.sourceLinks.length || d.targetLinks.length; });

                // ... the bar
                var bar = node.append('rect')
                    .attr('height', function(d) { return d.dy; })
                    .attr('width', options.nodeWidth)
                    .style('fill', options.colorInactive)
                    .style('shape-rendering', 'crispEdges');
                bar.append('title')
                    .text(function(d) { return d.name ? d.name + '\n' + d.value : d.value; });
                bar.filter(function(d) { return d.active; })
                    .style('fill', options.colorActive);

                // ... the inner value of the bar
                node.filter(function(d) { return d.display_value; })
                    .append('text')
                    .text(function(d) { return d.display_value; })
                    .attr('x', 0)
                    .attr('y', function(d) { return d.dy / 2; })
                    .attr('dx', '.5em')
                    .attr('dy', '.35em')
                    .style('font-size', options.fontSize)
                    .style('font-family', options.fontFamily)
                    .style('fill', '#fff')
                    .style('pointer-events', 'none');

                // Add the node names to the left and right of the bars
                name.all = node.filter(function(d) { return d.name; })
                    .append('text')
                    .text(function(d) { return d.name; })
                    .attr('x', 0)
                    .attr('y', function(d) { return d.dy / 2; })
                    .attr('dy', '.35em')
                    .attr('class', 'left')
                    .style('pointer-events', 'none')
                    .style('font-size', options.fontSize)
                    .style('font-family', options.fontFamily);
                name.left = name.all.filter(function(d) { return d.x < width / 2;})
                    .attr('class', 'name name-left')
                    .attr('text-anchor', 'end')
                    .attr('dx', -offset.margin);
                name.right = name.all.filter(function(d) { return d.x > width / 2;})
                    .attr('class', 'name name-right')
                    .attr('text-anchor', 'start')
                    .attr('dx', options.nodeWidth + offset.margin);
                if (inverse) {
                    name.left.attr('text-anchor', 'start')
                        .attr('dx', options.nodeWidth + offset.margin);
                    name.right.attr('text-anchor', 'end')
                        .attr('dx', -offset.margin);
                }

                // Rescale the sankey diagram to leave place to the left and right
                // for the node names
                //
                // NAME | <-- offset.margin --> SANKEY <-- offset.margin --> | NAME
                //      ^- offset.left                         offset.right -^
                //
                adjustOffset(name, offset, width);
                adjustScale(scale, width, offset, inverse);

                node.attr('transform', function(d) { return 'translate(' + scale(d.x) + ',' + d.y + ')'; });

                // Add the links
                var path = sankey.link(
                    scale,
                    inverse ? -options.nodeWidth : 0,
                    inverse ? options.nodeWidth : 0
                );
                var link = canvas.append('g').selectAll('.link')
                    .data(data.links)
                    .enter().append('path')
                    .attr('class', 'link')
                    .attr('d', path)
                    .attr('style', function(d) { return 'stroke: #000; stroke-opacity: 0.2; fill: none; stroke-width: ' + Math.round(Math.max(1, d.dy)) + 'px'; })
                    .sort(function(a, b) { return b.dy - a.dy; });

                link.append('title')
                    .text(function(d) { return d.value; });

                // Fade-Effect on mouseover
                if (interactive) {
                    node.on('mouseover', function(d) {
                    	link.transition()
                            .duration(700)
                    		.style('opacity', 0.1);
                    	link.filter(function(s) { return d.id == s.source.id; })
                            .transition()
                            .duration(700)
                    		.style('opacity', 1);
                    	link.filter(function(t) { return d.id == t.target.id; })
                            .transition()
                            .duration(700)
                    		.style('opacity', 1);
                    });
                    node.on('mouseout', function(d) {
                        link.transition()
                            .duration(700)
                    		.style('opacity', 1);
                    });
                    link.on('mouseover', function(d) {
                    	link.filter(function(s) { return s != d; })
                            .transition()
                            .duration(700)
                    		.style('opacity', 0.1);
                    });
                    link.on('mouseout', function(d) {
                        link.transition()
                            .duration(700)
                    		.style('opacity', 1);
                    });
                }

                // Make nodes moveable
                if (interactive) {
                    bar.style('cursor', 'move');
                    node.call(
                        d3.behavior.drag()
                            .origin(function(d) { return d; })
                            .on('dragstart', function() { this.parentNode.appendChild(this); })
                            .on('drag', function(d) {
                                d3.select(this).attr('transform', 'translate(' + scale(d.x) + ',' + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ')');
                                sankey.relayout();
                                link.attr('d', path);
                            })
                    );
                }

                // Relayout on resize
                if (interactive) {
                    d3.select(window).on('resize.sankey', function() {
                        if (node && link && path) {
                            // Resize
                            width = $(container).width() - margin.left - margin.right;
                            svg.attr('width', width + margin.left + margin.right);

                            adjustOffset(name, offset, width);
                            adjustScale(scale, width, offset, inverse);
                            node.attr('transform', function(d) { return 'translate(' + scale(d.x) + ',' + d.y + ')'; });
                            path = sankey.link(
                                scale,
                                inverse ? -options.nodeWidth : 0,
                                inverse ? options.nodeWidth : 0
                            );
                            link.attr('d', path);
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
