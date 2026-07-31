const path = '../../../../src/onegov/org';
const chart = require(path + '/assets/js/topic-chart');

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
