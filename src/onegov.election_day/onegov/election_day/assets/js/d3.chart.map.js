//
// A map.
//
(function(root, factory) {
  if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = factory;
  } else {
    root.ballotMap = factory(root.d3, root.topojson);
  }
}(this, function(d3, topojson) {
    return function(params) {
        var data = {};
        var mapdata = {};
        var canton = '';
        var margin = {top: 20, right: 10, bottom: 20, left: 10};
        var height = 0;
        var width = 0;
        var interactive = false;
        var yay = 'Yay';
        var nay = 'Nay';
        var expats = 'Expats';
        var options = {
            legendHeight: 10,
            legendMargin: 30,
            fontSizePx: 14,
            fontFamily: 'sans-serif'
        };

        if (params) {
            if (params.data) data = params.data;
            if (params.mapdata) mapdata = params.mapdata;
            if (params.canton) canton = params.canton;
            if (params.interactive) interactive = params.interactive;
            if (params.width) width = params.width;
            if (params.yay) yay = params.yay;
            if (params.nay) nay = params.nay;
            if (params.expats) expats = params.expats;
            if (params.options) options = params.options;
        }

        var isUndefined = function(obj) {
            return obj === void 0;
        };

        var chart = function(container) {

            // Try to read a default width from the container if none is given
            if ((typeof $ !== 'undefined') && !width) {
                width = $(container).width();
            }

            var svg = d3.select(container).append('svg')
                .attr('xmlns', 'http://www.w3.org/2000/svg')
                .attr('version', '1.1')
                .attr('width', width);

            if (data && mapdata.transform) {

                var path = d3.geo.path().projection(null);

                svg.append('defs')
                   .append('pattern')
                       .attr('id', 'uncounted')
                       .attr('patternUnits', 'userSpaceOnUse')
                       .attr('width', 4)
                       .attr('height', 4)
                   .append('path')
                       .attr('d', 'M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2')
                       .attr('stroke', '#999')
                       .attr('stroke-width', 1);

                var scale = d3.scale.linear()
                    .domain([30, 49.9999999, 50.000001, 70])
                    .range(['#ca0020', '#f4a582', '#92c5de', '#0571b0']);

                // Add tooltips
                var tooltip = null;
                if (interactive) {
                    tooltip = d3.tip()
                        .attr('class', 'd3-tip')
                        .direction(function(d) {
                            var b = this.getBBox();
                            var p = this.parentNode.getBBox();
                            return ((b.y - p.y > p.y + p.height - b.y - b.height) ? 'n' : 's') +
                                   ((b.x - p.x > p.x + p.width - b.x - b.width) ? 'w' : 'e');
                        })
                        .html(function(d) {
                            if (isUndefined(d.properties.result) ||
                                isUndefined(d.properties.result.yeas_percentage)) {
                                return '<strong>' + d.properties.name + '</strong>';
                            }
                            var yeas_percentage =  Math.round(d.properties.result.yeas_percentage * 100) / 100;
                            var nays_percentage =  Math.round(d.properties.result.nays_percentage * 100) / 100;

                            // use symbols to avoid text which we would have to translate
                            // also, only show the winning side, not both
                            if (yeas_percentage > nays_percentage) {
                                return [
                                    '<strong>' + d.properties.name + '</strong>',
                                    '<i class="fa fa-thumbs-up"></i> ' + yeas_percentage + '%'
                                ].join('<br/>');
                            } else {
                                return [
                                    '<strong>' + d.properties.name + '</strong>',
                                    '<i class="fa fa-thumbs-down"></i> ' + nays_percentage + '%'
                                ].join('<br/>');
                            }
                        });
                }

                // Add municipalties
                mapdata.transform.translate=[0,0];
                var municipalities = svg.append('g')
                    .attr('class', 'municipality')
                    .style('fill', 'transparent')
                    .selectAll('path')
                    .data(
                        topojson.feature(mapdata, mapdata.objects.municipalities).features
                    )
                    .enter().append('path')
                    .attr('d', path)
                    .attr('fill', function(d) {
                        // store the result for the tooltip
                        d.properties.result = data[d.properties.id];
                        if (!isUndefined(d.properties.result)) {
                            if (d.properties.result.counted) {
                                return scale(d.properties.result.yeas_percentage);
                            } else {
                                return 'url(#uncounted)';
                            }
                        }
                    })
                    .attr('class', function(d) {
                        if (!isUndefined(d.properties.result)) {
                            if (d.properties.result.counted) {
                                return 'counted';
                            } else {
                                return 'uncounted';
                            }
                        }
                    });
                if (interactive) {
                    municipalities
                        .on('mouseover.tooltip', tooltip.show)
                        .on('mouseout.tooltip', tooltip.hide)
                        .on('mouseover.highlight', function(d) {
                            // http://stackoverflow.com/a/4006353/3690178
                            if (!d3.select(this).classed('selected')) {
                              d3.select(this).classed('selected', true);
                              $(this).parent(this).prepend(this);
                            }
                        })
                        .on('mouseout.highlight', function() {
                            d3.select(this).classed('selected', false);
                        })
                        .on('click', tooltip.show);
                }

                // Add lakes
                if (mapdata.objects.lakes !== undefined) {
                    svg.append('g')
                        .attr('class', 'lake')
                        .style('fill', '#FFF')
                        .style('stroke', '#999')
                        .style('stroke-width', '1px')
                        .selectAll('path')
                        .data(
                            topojson.feature(mapdata, mapdata.objects.lakes).features
                        )
                        .enter().append('path')
                        .attr('d', path);
                }

                // Add Borders
                svg.append('g')
                    .append('path')
                    .datum(topojson.mesh(
                        mapdata, mapdata.objects.municipalities, function(a, b) {
                            return a !== b;
                        }
                    ))
                    .attr('class', 'border')
                    .style('stroke-width', '1px')
                    .style('fill', 'none')
                    .attr('d', path);

                // Add the expats
                var bboxMap = svg[0][0].getBBox();
                if (0 in data) {
                    // the globe is 230px unscaled, we place it in the lower
                    // left corner for now
                    globe = svg.append('g')
                        .attr(
                            'transform',
                            'translate(0,' + Math.round(bboxMap.y + 3 / 4 * bboxMap.height) +  ')'
                        )
                        .property('__data__', {
                            'properties': {
                              'name': expats,
                              'result': data[0]
                            }
                          }
                        )
                        .append('g')
                        .attr(
                            'transform',
                            'scale(' + (bboxMap.width - bboxMap.x)/230/10 + ')'
                        );

                    globe.append('g')
                        .append('path')
                        .attr('fill', 'white')
                        .attr('fill', scale(data[0].yeas_percentage))
                        .attr('stroke', 'none')
                        .attr('d', "M 306.11308,163.17191 C 306.11308,224.93199 256.04569,274.99881 194.2941,274.99881 C 132.53683,274.99881 82.472286,224.93144 82.472286,163.17191 C 82.472286,101.41465 132.53683,51.352937 194.2941,51.352937 C 256.04569,51.352937 306.11308,101.41465 306.11308,163.17191 L 306.11308,163.17191 z ");

                    globe.append('g')
                        .append('path')
                        .attr('fill', 'white')
                        .attr('stroke', 'none')
                        .attr('d', "M 301.80858,145.26395 C 301.80858,146.75216 301.80858,145.26395 301.80858,145.26395 L 298.72167,148.76043 C 296.82954,146.53066 294.70514,144.65552 292.54788,142.6971 L 287.81244,143.39391 L 283.48603,138.50325 L 283.48603,144.55581 L 287.19268,147.36059 L 289.65982,150.15461 L 292.95689,146.42584 C 293.78682,147.98034 294.60542,149.53484 295.4297,151.08934 L 295.4297,155.74772 L 291.71737,159.94101 L 284.92382,164.6045 L 279.7788,169.73876 L 276.48173,165.99868 L 278.13026,161.80539 L 274.83829,158.07663 L 269.2786,146.19302 L 264.54315,140.83782 L 263.30364,142.232 L 265.16235,148.9927 L 268.65884,152.95371 C 270.65577,158.7185 272.63119,164.22834 275.25353,169.73876 C 279.31993,169.73876 283.15348,169.30708 287.19212,168.79836 L 287.19212,172.06258 L 282.25161,184.18129 L 277.72068,189.30422 L 274.01403,197.23758 C 274.01403,201.58609 274.01403,205.9346 274.01403,210.28255 L 275.25353,215.41681 L 273.19543,217.74061 L 268.65884,220.53972 L 263.92341,224.50074 L 267.84023,228.92687 L 262.48504,233.59602 L 263.51382,236.61663 L 255.48075,245.71191 L 250.13121,245.71191 L 245.60029,248.51102 L 242.71223,248.51102 L 242.71223,244.78226 L 241.48405,237.31344 C 239.89047,232.63296 238.23116,227.9859 236.54354,223.33883 C 236.54354,219.90863 236.74805,216.51186 236.95312,213.08222 L 239.01691,208.42383 L 236.12886,202.82504 L 236.33903,195.13527 L 232.4222,190.70916 L 234.38061,184.30253 L 231.194,180.68706 L 225.62865,180.68706 L 223.77559,178.59043 L 218.21589,182.08974 L 215.95326,179.52006 L 210.80258,183.94845 C 207.3061,179.9846 203.80396,176.02358 200.30237,172.06258 L 196.18614,162.27049 L 199.89278,156.68303 L 197.83467,154.35412 L 202.35992,143.62673 C 206.07791,139.00178 209.96132,134.56488 213.88948,130.11157 L 220.89322,128.2472 L 228.71611,127.31756 L 234.07131,128.71739 L 241.68913,136.40151 L 244.367,133.37523 L 248.068,132.91068 L 255.07172,135.2396 L 260.42692,135.2396 L 264.13357,131.97537 L 265.78211,129.64647 L 262.06978,127.31756 L 255.89033,126.85302 C 254.1755,124.47426 252.58192,121.97369 250.54589,119.86007 L 248.48211,120.7897 L 247.65784,126.85302 L 243.95118,122.65974 L 243.13258,117.99059 L 239.01634,114.7377 L 237.36214,114.7377 L 241.48348,119.39609 L 239.83495,123.58937 L 236.54296,124.51901 L 238.60109,120.32573 L 234.88876,118.46702 L 231.60246,114.73826 L 225.41733,116.13245 L 224.59873,117.99115 L 220.89208,120.32573 L 218.83396,125.45432 L 213.68894,128.0155 L 211.42064,125.45432 L 208.9535,125.45432 L 208.9535,117.06208 L 214.30869,114.26297 L 218.42494,114.26297 L 217.595,111.00443 L 214.30869,107.74021 L 219.86329,106.57263 L 222.9502,103.08182 L 225.41733,98.882871 L 229.95394,98.882871 L 228.7144,95.62432 L 231.60246,93.759947 L 231.60246,97.488693 L 237.77625,98.882871 L 243.95005,93.759947 L 244.36474,91.425367 L 249.71426,87.699449 C 247.77794,87.940214 245.84162,88.116965 243.94949,88.631919 L 243.94949,84.433535 L 246.0076,79.772313 L 243.94949,79.772313 L 239.4265,83.9656 L 238.18697,86.297343 L 239.4265,89.56439 L 237.3627,95.15185 L 234.07073,93.287476 L 231.194,90.028927 L 226.65742,93.287476 L 225.00889,85.832808 L 232.83178,80.707051 L 232.83178,77.907937 L 237.77739,74.646556 L 245.60029,72.779348 L 250.95548,74.646556 L 260.83594,76.510932 L 258.3688,79.304945 L 253.0136,79.304945 L 258.3688,84.898071 L 262.48504,80.239681 L 263.73531,78.190059 C 263.73531,78.190059 279.52444,92.341409 288.54777,107.82121 C 297.5711,123.30613 301.80858,141.55729 301.80858,145.26395 z M 199.83161,80.239681 L 199.41691,83.033696 L 202.30497,84.898071 L 207.23982,81.636688 L 204.77269,78.839843 L 201.4756,80.707051 L 199.83274,80.239681 M 204.36252,61.131394 L 193.65215,56.935274 L 181.30398,58.332281 L 166.06268,62.525568 L 163.18029,65.32468 L 172.65172,71.847444 L 172.65172,75.576194 L 168.94506,79.304945 L 173.89068,89.099855 L 177.17698,87.229814 L 181.30398,80.707051 C 187.66586,78.740138 193.37003,76.510932 199.41691,73.714086 L 204.36252,61.130827 M 215.4825,100.28611 L 213.83396,96.087154 L 210.94591,97.02189 L 211.77585,102.14482 L 215.4825,100.28611 M 217.12537,99.345704 L 216.3011,104.9445 L 220.83202,104.00976 L 224.12399,100.7512 L 221.2416,97.952096 C 220.27346,95.373923 219.16139,92.967399 217.94963,90.494596 L 215.4825,90.494596 L 215.4825,93.288609 L 217.12537,95.152987 L 217.12537,99.346273 M 156.18166,187.90948 L 152.88459,181.38161 L 146.70796,179.9846 L 143.41371,171.13293 L 135.17897,172.06258 L 128.18033,166.93965 L 120.76418,173.46241 L 120.76418,174.49119 C 118.52083,173.84367 115.76307,173.75529 113.76556,172.5271 L 112.11703,167.86872 L 112.11703,162.74012 L 107.1765,163.20465 C 107.58893,159.94045 107.99795,156.6819 108.4132,153.41826 L 105.52797,153.41826 L 102.64842,157.147 L 99.763202,158.54117 L 95.644126,156.21736 L 95.231709,151.08877 L 96.055976,145.49565 L 102.23543,140.83725 L 107.17595,140.83725 L 107.99738,138.03814 L 114.17401,139.43232 L 118.70495,145.03111 L 119.5292,135.70357 L 127.35438,129.1808 L 130.23677,122.18784 L 136.00154,119.85892 L 139.29578,115.20054 L 146.70626,113.7956 L 150.41575,108.20814 C 146.70908,108.20814 143.00243,108.20814 139.29578,108.20814 L 146.29667,104.94393 L 151.23434,104.94393 L 158.23808,102.60935 L 159.06234,99.821009 L 156.58954,97.486429 L 153.70714,96.551693 L 154.53142,93.757672 L 152.4733,89.56439 L 147.52996,91.423101 L 148.35424,87.697183 L 142.58945,84.432968 L 138.06136,92.352173 L 138.47095,95.15128 L 133.94285,97.021321 L 131.05763,103.07899 L 129.82378,97.48586 L 121.9986,94.221643 L 120.76193,90.02836 L 131.05763,83.965034 L 135.58856,79.771747 L 136.00097,74.64599 L 133.531,73.24615 L 130.23677,72.778782 L 128.17863,77.907371 C 128.17863,77.907371 124.73484,78.582082 123.84939,78.800753 C 112.54134,89.221088 89.692968,111.71539 84.384795,154.18133 C 84.594969,155.16592 88.232512,160.87519 88.232512,160.87519 L 96.879678,165.9981 L 105.52685,168.33269 L 109.23633,172.99617 L 114.99828,177.18945 L 118.29252,176.72492 L 120.7625,177.83697 L 120.7625,178.5893 L 117.47052,187.4438 L 114.99772,191.17256 L 115.82198,193.0426 L 113.76387,200.02422 L 121.17717,213.54506 L 128.58766,220.07293 L 131.88473,224.7313 L 131.47005,234.52339 L 133.94285,240.11085 L 131.47005,250.83256 C 131.47005,250.83256 131.2763,250.76627 131.59184,251.83924 C 131.91021,252.91279 144.78636,260.0604 145.60496,259.45198 C 146.42074,258.83222 147.11811,258.29007 147.11811,258.29007 L 146.29667,255.96624 L 149.58865,252.70204 L 150.82533,249.43783 L 156.18052,247.56779 L 160.29676,237.31117 L 159.06291,234.52282 L 161.93964,230.32953 L 168.1191,228.92458 L 171.41616,221.4671 L 170.5919,212.15088 L 175.53241,205.15792 L 176.35668,198.16496 C 169.59598,194.81237 162.89081,191.36008 156.18052,187.90834 M 147.11981,82.101225 L 151.23605,84.898071 L 154.53312,84.898071 L 154.53312,81.636688 L 150.41689,79.772313 L 147.11981,82.101225 M 136.41509,78.375307 L 134.35414,83.501064 L 138.47321,83.501064 L 140.53416,78.839843 C 142.31015,77.583896 144.07766,76.320019 145.88651,75.111092 L 150.0056,76.510932 C 152.74975,78.375307 155.49392,80.239681 158.24034,82.101225 L 162.36169,78.375307 L 157.82792,76.510932 L 155.76696,72.314812 L 147.94407,71.382342 L 147.53166,69.050598 L 143.825,69.985335 L 142.17987,73.247283 L 140.11891,69.051164 L 139.29748,70.915539 L 139.70989,75.57676 L 136.41509,78.375307 M 151.23605,66.718855 L 153.297,64.857312 L 157.41607,63.924841 C 160.23728,62.55276 163.06983,61.628787 166.06324,60.660625 L 164.42037,57.86378 L 159.1037,58.627431 L 156.5918,61.130827 L 152.45064,61.731324 L 148.7689,63.460305 L 146.97932,64.325927 L 145.88651,65.789216 L 151.23605,66.718855 M 158.23978,111.00215 L 160.71258,107.2734 L 157.00309,104.47939 L 158.23978,111.00215");

                    if (interactive) {
                        globe
                            .on('mouseover', tooltip.show)
                            .on('mouseout', tooltip.hide)
                            .on('click', tooltip.show);
                    }
                }

                // Add the the legend (we need to up/downscale the elements)
                var unitScale = d3.scale.linear()
                    .rangeRound([0, (bboxMap.width - bboxMap.x) / (width - margin.left - margin.right)]);
                var legendValues = [80, 70, 60, 50.001, 49.999, 40, 30, 20];
                var legendScale = d3.scale.ordinal()
                    .domain(legendValues)
                    .rangeRoundBands([0.2 * (bboxMap.width - bboxMap.x), 0.8 * (bboxMap.width - bboxMap.x)]);
                var legend = svg.append('g')
                    .attr('transform', function(d) {
                        return 'translate(0,' + Math.round(bboxMap.y + bboxMap.height + unitScale(options.legendMargin)) + ')';
                    });
                var legendItems = legend.selectAll('.legend_item')
                    .data(legendValues).enter()
                    .append('rect')
                    .attr('x', function(d) {return legendScale(d);})
                    .attr('width', legendScale.rangeBand())
                    .attr('height', unitScale(options.legendHeight))
                    .style('fill', function(d) {return scale(d);});
                var text_yay = legend.append('text')
                    .attr('x', legendScale(80))
                    .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                    .style('font-size', unitScale(options.fontSizePx) + 'px')
                    .style('font-family', options.fontFamily)
                    .text(yay);
                var text_nay = legend.append('text')
                    .attr('x', legendScale(20) + legendScale.rangeBand())
                    .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                    .style('text-anchor', 'end')
                    .style('font-size',unitScale(options.fontSizePx) + 'px')
                    .style('font-family', options.fontFamily)
                    .text(nay);

                // Set size
                bbox = svg[0][0].getBBox();
                height = Math.floor(width * (bbox.height/bbox.width));
                svg.attr('height', height)
                   .attr('viewBox',
                    [
                      bbox.x - unitScale(margin.left),
                      bbox.y - unitScale(margin.top),
                      bbox.width + unitScale(margin.left) + unitScale(margin.right),
                      bbox.height + unitScale(margin.top) + unitScale(margin.bottom)
                    ].join(' ')
                );


                if (interactive) {
                    // Add tooltips
                    svg.call(tooltip);

                    // Relayout on resize
                    d3.select(window).on('resize.ballotmap', function() {
                        width = $(container).width();
                        unitScale.rangeRound([bboxMap.x, (bboxMap.width - bboxMap.x) / (width - margin.left - margin.right)]);
                        legendScale.rangeRoundBands([0.2 * (bboxMap.width - bboxMap.x), 0.8 * (bboxMap.width - bboxMap.x)]);
                        legend.attr('transform', function(d) {
                                return 'translate(0,' + Math.round(bboxMap.y + bboxMap.height + unitScale(options.legendMargin)) + ')';
                            });
                        legendItems.attr('x', function(d) {return legendScale(d);})
                            .attr('width', legendScale.rangeBand())
                            .attr('height', unitScale(options.legendHeight))
                            .style('fill', function(d) {return scale(d);});
                        text_yay.attr('x', legendScale(80))
                            .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                            .style('font-size', unitScale(options.fontSizePx) + 'px');
                        text_nay.attr('x', legendScale(20) + legendScale.rangeBand())
                            .attr('y', unitScale(options.legendHeight + 1.5 * options.fontSizePx))
                            .style('font-size', unitScale(options.fontSizePx) + 'px');

                        bbox = svg[0][0].getBBox();

                        height = Math.floor(width * (bbox.height/bbox.width));


                        svg.attr('width', width)
                           .attr('height', height)
                           .attr('viewBox',
                            [
                              bbox.x - unitScale(margin.left),
                              bbox.y - unitScale(margin.top),
                              bbox.width + unitScale(margin.left) + unitScale(margin.right),
                              bbox.height + unitScale(margin.top) + unitScale(margin.bottom)
                            ].join(' ')
                        );
                    });
                }
            }
            return chart;
        };

        chart.width = function() {
            return width;
        };

        chart.height = function() {
            return height;
        };

        return chart;
    };
}));
