/*
    Renders the topic hierarchy as an org chart, into the element with the
    'information-architecture' class whose 'data-url' points to a json view returning a
    flat list of nodes.
*/

const escaper = document.createElement('div');

function escape_html(text) {
    escaper.textContent = text;
    // innerHTML does not escape quotes, which we need for attributes
    return escaper.innerHTML.replace(/"/g, '&quot;');
}

// reduces the nodes to the branch below the given id, which becomes the
// new root - without an id the whole chart is returned
function branch(nodes, root_id) {
    const root = root_id && nodes.find((node) => node.id === root_id);
    if (!root) {
        return nodes;
    }

    const children = {};
    nodes.forEach((node) => {
        children[node.parentId] = children[node.parentId] || [];
        children[node.parentId].push(node);
    });

    // the root of a chart is the node without a parent
    const result = [Object.assign({}, root, {parentId: null})];
    for (let i = 0; i < result.length; i++) {
        (children[result[i].id] || []).forEach((child) => result.push(child));
    }

    return result;
}

// icon glyphs as text; WebKit misplaces svg/backgrounds in a foreignObject
// https://github.com/bkrem/react-d3-tree/issues/284
const DRILLUP_ICON = '\uf062'; // arrow-up
const DRILLDOWN_ICON = '\uf0e8'; // sitemap

// the buttons are a screen affordance, they have no place in an export
function node_buttons(node, view) {
    if (view.exporting) {
        return '';
    }

    let buttons = '';

    // only the root of a drilled down chart has a level above it
    if (
        view.parent_id &&
        node.data.id === view.root_id
    ) {
        buttons += `
            <span class="drillup" role="button" tabindex="0"
                  data-drillup="${escape_html(view.parent_id)}"
                  title="${escape_html(view.drillup_label)}">${DRILLUP_ICON}</span>
        `;
    }

    // the root is the branch already, drilling into it changes nothing
    if (node.data._directSubordinates && node.depth > 0) {
        buttons += `
            <span class="drilldown" role="button" tabindex="0"
                  data-drilldown="${escape_html(node.data.id)}"
                  title="${escape_html(view.drilldown_label)}">${DRILLDOWN_ICON}</span>
        `;
    }

    return buttons;
}

function node_content(node, view) {
    const name = node.data.name;
    // long words don't fit into a node, so we let the browser hyphenate them
    const hyphens = name.split(' ').some((word) => word.length > 15);
    const classes = ['d3-orgchart-node'];
    const restricted = !node.data.published || node.data.access !== 'public';

    if (hyphens) {
        classes.push('hyphens');
    }
    if (!node.data.published) {
        classes.push('unpublished');
    } else if (node.data.access !== 'public') {
        classes.push('restricted');
    }

    // the exported image is a serialized copy of the svg, which does not
    // include the stylesheet - so the looks of a node have to be inline
    // (the themes override them with !important for the screen)
    const style = [
        `width:${node.width}px`,
        `height:${node.height}px`,
        'box-sizing:border-box',
        'padding:.7rem 1rem',
        'background:#fff',
        `border:2px ${restricted ? 'dashed' : 'solid'} #e0e0e0`,
        'border-radius:.7rem',
        'color:#444',
        'font-weight:bold',
        'overflow:hidden',
        hyphens ? 'hyphens:auto' : ''
    ].join(';');

    // long titles are clipped by the box, the tooltip shows them in full
    return `
        <a href="${escape_html(node.data.url)}">
            <div class="${classes.join(' ')}" style="${style}"
                 title="${escape_html(name)}">
                <span>${escape_html(name)}</span>
                ${node_buttons(node, view)}
            </div>
        </a>
    `;
}

// browsers refuse to draw canvases beyond ~16'000 pixels per side and
// run out of memory before that, at four bytes per pixel
const MAX_EXPORT_SIZE = 15000;
const MAX_EXPORT_AREA = 80 * 1000 * 1000;
// four pixels per pixel of the chart yields roughly 400 dpi
const EXPORT_SCALE = 4;
const EXPORT_MARGIN = 50;

/*
    Turns the bounds of the chart into the size of the exported image. The
    scale multiplies the natural size, limited by what the browser can draw
    - below 1 the chart would be shrunk into the image, which only the svg
    export can hold in full.
*/
function export_dimensions(bounds) {
    const width = bounds.right - bounds.left + 2 * EXPORT_MARGIN;
    const height = bounds.bottom - bounds.top + 2 * EXPORT_MARGIN;

    const scale = Math.min(
        EXPORT_SCALE,
        MAX_EXPORT_SIZE / width,
        MAX_EXPORT_SIZE / height,
        Math.sqrt(MAX_EXPORT_AREA / (width * height))
    );

    return {
        width: width,
        height: height,
        scale: scale,
        fits: scale >= 1
    };
}

// the message belongs to the actions, the chart itself is covered by the svg
function set_message(text) {
    const message = document.querySelector('.chart-message');
    if (message) {
        message.textContent = text || '';
        message.hidden = !text;
    }
}

// the chart uses the 'top' layout, where x is the center of a node
function chart_bounds(chart) {
    const bounds = {
        left: Infinity, right: -Infinity, top: Infinity, bottom: -Infinity
    };

    chart.getChartState().root.descendants().forEach((node) => {
        bounds.left = Math.min(bounds.left, node.x - node.width / 2);
        bounds.right = Math.max(bounds.right, node.x + node.width / 2);
        bounds.top = Math.min(bounds.top, node.y);
        bounds.bottom = Math.max(bounds.bottom, node.y + node.height);
    });

    return bounds;
}

/*
    Both exports serialize the svg of the chart, which is only as large as
    the viewport and holds the pan and zoom of the screen - everything
    outside of it would be cut off, so it is grown to the whole chart.
*/
function expand_chart(chart, container, view, bounds, size) {
    const state = chart.getChartState();

    // the enlarged chart would push the page around, so it is clipped
    container.style.overflow = 'hidden';
    state.svg.attr('width', size.width).attr('height', size.height);
    state.centerG.attr('transform', 'translate(0,0)');
    state.chart.attr(
        'transform',
        `translate(${EXPORT_MARGIN - bounds.left},${EXPORT_MARGIN - bounds.top})`
    );

    // the buttons are a screen affordance, they have no place in an export
    view.exporting = true;
    chart.restyleForeignObjectElements();
}

function restore_chart(chart, container, view) {
    view.exporting = false;
    container.style.overflow = '';
    chart.render().fit();
}

/*
    Exports the visible nodes as an image, at the natural size of the chart
    - d3's own 'full' export fits it into the viewport first, which leaves
    large charts unreadable no matter the resolution.
*/
function export_image(chart, container, view) {
    const bounds = chart_bounds(chart);
    const size = export_dimensions(bounds);

    if (!size.fits) {
        set_message(container.dataset.exportErrorMessage);
        return;
    }
    set_message('');

    expand_chart(chart, container, view, bounds, size);

    // serialized in a later tick, so the chart is restored once it loaded
    chart.exportImg({
        scale: size.scale,
        onLoad: () => restore_chart(chart, container, view)
    });
}

// vectors have no pixels to run out of, only the size matters here
function export_svg(chart, container, view) {
    const bounds = chart_bounds(chart);

    expand_chart(chart, container, view, bounds, export_dimensions(bounds));
    chart.exportSvg();
    restore_chart(chart, container, view);
}

function init_information_architecture(container) {
    // what the chart currently shows: all nodes, drilled down to root_id
    const view = {
        nodes: [],
        root_id: null,
        parent_id: null,
        exporting: false,
        drilldown_label: container.dataset.drilldownLabel || '',
        drillup_label: container.dataset.drillupLabel || ''
    };

    const chart = new d3.OrgChart()
        .container(container)
        .nodeWidth(() => 220)
        .nodeHeight(() => 120)
        .childrenMargin(() => 60)
        .siblingsMargin(() => 20)
        // the level is the depth of the deepest expanded node, so 1 shows
        // two levels: the root and its children
        .initialExpandLevel(1)
        .imageName(container.dataset.imageName || 'information-architecture')
        .nodeContent((node) => node_content(node, view));

    const reset_buttons = document.querySelectorAll(
        '[data-chart-action="reset"]'
    );

    const draw = () => {
        const root = view.nodes.find((node) => node.id === view.root_id);

        // without a level above, the chart shows everything there is
        view.parent_id = root ? root.parentId : null;

        chart.data(branch(view.nodes, view.root_id)).render().fit();
        reset_buttons.forEach((button) => {
            button.hidden = !view.parent_id;
        });
    };

    const actions = {
        expand: () => chart.expandAll().fit(),
        collapse: () => chart.collapseAll().fit(),
        fit: () => chart.fit(),
        export: () => export_image(chart, container, view),
        // the svg keeps the nodes as html inside foreignObject elements,
        // which browsers render, but most vector editors do not
        'export-svg': () => export_svg(chart, container, view),
        reset: () => {
            view.root_id = null;
            draw();
        }
    };

    document.querySelectorAll('[data-chart-action]').forEach((button) => {
        const action = actions[button.dataset.chartAction];
        if (action) {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                action();
            });
        }
    });

    // the buttons live inside the node links, whose default is not wanted
    container.addEventListener('click', (event) => {
        const down = event.target.closest('[data-drilldown]');
        const up = event.target.closest('[data-drillup]');

        if (down || up) {
            event.preventDefault();
            view.root_id = down ? down.dataset.drilldown : up.dataset.drillup;
            draw();
        }
    });

    // the drill affordances are spans, so they need explicit keyboard support
    container.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        const target = event.target.closest('[data-drilldown], [data-drillup]');
        if (target) {
            event.preventDefault();
            target.click();
        }
    });

    fetch(container.dataset.url)
        .then((response) => response.json())
        .then((data) => {
            view.nodes = data.nodes;
            draw();
        })
        .catch(() => {
            const info = container.querySelector('.loading-info');
            if (info) {
                info.classList.add('error');
                info.textContent = container.dataset.errorMessage;
            }
        });
}

document.addEventListener('DOMContentLoaded', () => {
    // the menu link shares the class, only the container carries the url
    const container = document.querySelector('.information-architecture[data-url]');
    if (container) {
        init_information_architecture(container);
    }
});

if (typeof module !== 'undefined') {
    module.exports = {
        export_dimensions: export_dimensions,
        chart_bounds: chart_bounds,
        export_svg: export_svg,
        node_content: node_content,
        branch: branch
    };
}
