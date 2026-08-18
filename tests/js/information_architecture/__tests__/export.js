const path = '../../../../src/onegov/org';
const chart = require(path + '/assets/js/information-architecture');

// a node is 220x90, the export adds a margin of 50 on every side
const bounds = function(width, height) {
    return {left: 0, right: width, top: 0, bottom: height};
};

// root -> a -> a1, a2 (a2 -> a21), root -> b
const nodes = [
    {id: 'root', parentId: null},
    {id: 'a', parentId: 'root'},
    {id: 'a1', parentId: 'a'},
    {id: 'a2', parentId: 'a'},
    {id: 'a21', parentId: 'a2'},
    {id: 'b', parentId: 'root'}
];

const ids = function(list) {
    return list.map((node) => node.id);
};

describe('Export dimensions', () => {
    it('exports the chart at its natural size', () => {
        const size = chart.export_dimensions(bounds(220, 90));
        expect(size.width).toBe(320);
        expect(size.height).toBe(190);
    });

    it('keeps the bounds of charts not starting at the origin', () => {
        const size = chart.export_dimensions(
            {left: -500, right: 500, top: -100, bottom: 100}
        );
        expect(size.width).toBe(1100);
        expect(size.height).toBe(300);
    });

    it('quadruples the resolution', () => {
        const size = chart.export_dimensions(bounds(1000, 500));
        expect(size.scale).toBe(4);
        expect(size.width * size.scale).toBe(4400);
        expect(size.fits).toBe(true);
    });

    it('limits the scale to the largest side a browser can draw', () => {
        // 3750 wide at a scale of 4 is exactly the limit
        expect(chart.export_dimensions(bounds(3650, 100)).scale).toBe(4);

        const wide = chart.export_dimensions(bounds(4900, 100));
        expect(wide.width).toBe(5000);
        expect(wide.scale).toBe(3);
        expect(wide.width * wide.scale).toBe(15000);

        const tall = chart.export_dimensions(bounds(100, 4900));
        expect(tall.height).toBe(5000);
        expect(tall.scale).toBe(3);
    });

    it('limits the scale to the largest area a browser can draw', () => {
        // 5000x4000 would fit the sides at a scale of 3, but not the area
        const size = chart.export_dimensions(bounds(4900, 3900));
        expect(size.width * size.height).toBe(20000000);
        expect(size.scale).toBe(2);
        expect(size.width * size.scale * size.height * size.scale).toBe(
            80000000);
        expect(size.fits).toBe(true);
    });

    it('does not fit charts too large for a canvas', () => {
        // too wide for a single side
        const wide = chart.export_dimensions(bounds(29900, 100));
        expect(wide.scale).toBeLessThan(1);
        expect(wide.fits).toBe(false);

        // sides small enough, but 96 of 80 megapixels
        const large = chart.export_dimensions(bounds(11900, 7900));
        expect(large.width * large.height).toBe(96000000);
        expect(large.scale).toBeLessThan(1);
        expect(large.fits).toBe(false);

        // right at the limit it still fits
        const limit = chart.export_dimensions(bounds(14900, 100));
        expect(limit.scale).toBe(1);
        expect(limit.fits).toBe(true);
    });
});

describe('Drill down', () => {
    it('shows the whole chart without a node', () => {
        expect(chart.branch(nodes, null)).toBe(nodes);
        expect(chart.branch(nodes)).toBe(nodes);
    });

    it('keeps the node and its descendants', () => {
        expect(ids(chart.branch(nodes, 'a')).sort()).toEqual(
            ['a', 'a1', 'a2', 'a21']);
    });

    it('makes the node the new root', () => {
        const branch = chart.branch(nodes, 'a');
        expect(branch[0].id).toBe('a');
        expect(branch[0].parentId).toBe(null);

        // the nodes of the full chart are left alone
        expect(nodes[1].parentId).toBe('root');
    });

    it('drills down to a leaf', () => {
        expect(ids(chart.branch(nodes, 'b'))).toEqual(['b']);
    });

    it('falls back to the whole chart for an unknown node', () => {
        expect(chart.branch(nodes, 'nope')).toBe(nodes);
    });
});

describe('Node content', () => {
    const node = function(data, depth) {
        return {width: 220, height: 90, depth: depth === undefined ? 1 : depth,
            data: Object.assign({
                name: 'Topic', url: '/topics/topic', access: 'public',
                published: true, id: 'topic-1', _directSubordinates: 0
            }, data)};
    };

    const view = {exporting: false, drilldown_label: 'Only this branch'};

    it('shows the full title as a tooltip', () => {
        const long = 'A topic with a title too long for the box';
        expect(chart.node_content(node({name: long}), view)).toContain(
            `title="${long}"`);
    });

    it('escapes the title in the text and the tooltip', () => {
        const html = chart.node_content(
            node({name: 'Foo & "Bar" <b>', url: '/a?b=1&c=2'}), view);
        expect(html).toContain('title="Foo &amp; &quot;Bar&quot; &lt;b&gt;"');
        expect(html).toContain('<span>Foo &amp; &quot;Bar&quot; &lt;b&gt;</span>');
        expect(html).not.toContain('<b>');
        expect(html).toContain('href="/a?b=1&amp;c=2"');
    });

    it('draws the icons inline, the icon fonts differ per theme', () => {
        const html = chart.node_content(node({_directSubordinates: 2}), view);
        expect(html).toContain('<svg');
        expect(html).not.toContain('<i class');
    });

    it('offers the drill down to nodes with children only', () => {
        expect(chart.node_content(node({}), view)).not.toContain('drilldown');

        const parent = chart.node_content(
            node({_directSubordinates: 2}), view);
        expect(parent).toContain('data-drilldown="topic-1"');
        expect(parent).toContain('title="Only this branch"');
    });

    it('leaves the root of the chart alone, it is the branch already', () => {
        expect(chart.node_content(node({_directSubordinates: 5}, 0), view))
            .not.toContain('drilldown');
    });

    it('leaves the drill down out of an export', () => {
        const html = chart.node_content(
            node({_directSubordinates: 2}), {exporting: true});
        expect(html).not.toContain('drilldown');
        expect(html).toContain('title="Topic"');
    });
});

describe('Drill up', () => {
    const node = function(id) {
        return {width: 220, height: 90, data: {
            name: 'Topic', url: '/t', access: 'public', published: true,
            id: id, _directSubordinates: 0}};
    };

    const view = function(root_id, parent_id) {
        return {
            exporting: false, root_id: root_id, parent_id: parent_id,
            drillup_label: 'Level above'
        };
    };

    it('offers the level above on the root of a branch', () => {
        const html = chart.node_content(node('a'), view('a', 'root'));
        expect(html).toContain('data-drillup="root"');
        expect(html).toContain('title="Level above"');
    });

    it('leaves the other nodes of the branch alone', () => {
        expect(chart.node_content(node('a1'), view('a', 'root'))).not.toContain(
            'drillup');
    });

    it('has nothing above the whole chart', () => {
        expect(chart.node_content(node('root'), view(null, null))).not.toContain(
            'drillup');
    });

    it('has nothing above the organisation, drilled up to it or not', () => {
        expect(chart.node_content(node('root'), view('root', null))).not.toContain(
            'drillup');
    });

    it('leaves the drill up out of an export', () => {
        const drilled = view('a', 'root');
        drilled.exporting = true;
        expect(chart.node_content(node('a'), drilled)).not.toContain('drillup');
    });
});

describe('Export of the whole chart', () => {
    // the nodes carry the layout of the chart, x is the center of a node
    const laid_out = function(x, y) {
        return {x: x, y: y, width: 220, height: 90};
    };

    // records what the export does to the chart instead of drawing it
    const fake_chart = function(laid_out_nodes) {
        const svg = {};
        const center = {};
        const group = {};
        const log = [];

        const attrs = function(target) {
            return {
                attr: function(name, value) {
                    target[name] = value;
                    return this;
                }
            };
        };

        return {
            svg: svg,
            center: center,
            group: group,
            log: log,
            getChartState: () => ({
                root: {descendants: () => laid_out_nodes},
                svg: attrs(svg),
                centerG: attrs(center),
                chart: attrs(group)
            }),
            restyleForeignObjectElements: () => log.push('restyle'),
            exportSvg: () => log.push('export'),
            render: function() {
                log.push('render');
                return this;
            },
            fit: function() {
                log.push('fit');
                return this;
            }
        };
    };

    it('measures the chart from its nodes', () => {
        const measured = chart.chart_bounds(fake_chart([
            laid_out(110, 0), laid_out(610, 150)
        ]));
        expect(measured).toEqual({left: 0, right: 720, top: 0, bottom: 240});
    });

    it('measures nodes left of the origin as well', () => {
        const measured = chart.chart_bounds(fake_chart([
            laid_out(-110, -50), laid_out(110, 0)
        ]));
        expect(measured).toEqual(
            {left: -220, right: 220, top: -50, bottom: 90});
    });

    it('grows the svg to the whole chart, the viewport would cut it', () => {
        const drawn = fake_chart([laid_out(110, 0), laid_out(610, 150)]);
        const container = {style: {}, dataset: {}};
        const view = {exporting: false};

        chart.export_svg(drawn, container, view);

        // the natural size of the chart, margins included
        expect(drawn.svg.width).toBe(820);
        expect(drawn.svg.height).toBe(340);

        // no pan and no zoom, the chart starts at the margin
        expect(drawn.group.transform).toBe('translate(50,50)');
        expect(drawn.center.transform).toBe('translate(0,0)');
    });

    it('restores the chart after the export', () => {
        const drawn = fake_chart([laid_out(110, 0)]);
        const container = {style: {overflow: ''}, dataset: {}};
        const view = {exporting: false};

        chart.export_svg(drawn, container, view);

        expect(drawn.log).toEqual(['restyle', 'export', 'render', 'fit']);
        expect(view.exporting).toBe(false);
        expect(container.style.overflow).toBe('');
    });
});
