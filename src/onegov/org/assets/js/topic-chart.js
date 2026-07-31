/*
    Renders the topic hierarchy (information architecture) as an org chart.

    The chart is drawn into the element with the 'topic-chart' class whose
    'data-url' points to a json view returning a flat list of nodes.
*/

function escape_html(text) {
    const div = document.createElement('div');
    div.textContent = text;
    // innerHTML does not escape quotes, which we need for attributes
    return div.innerHTML.replace(/"/g, '&quot;');
}

/*
    Reduces the flat list of nodes to the branch below the given id, which
    becomes the new root. Without an id the whole chart is returned.
*/
function branch(nodes, root_id) {
    if (!root_id) {
        return nodes;
    }

    const children = {};
    nodes.forEach((node) => {
        children[node.parentId] = children[node.parentId] || [];
        children[node.parentId].push(node);
    });

    const root = nodes.filter((node) => node.id === root_id)[0];
    if (!root) {
        return nodes;
    }

    // the root of a chart is the node without a parent
    const result = [Object.assign({}, root, {parentId: null})];
    for (let i = 0; i < result.length; i++) {
        (children[result[i].id] || []).forEach((child) => result.push(child));
    }

    return result;
}

// drawn inline, the icon fonts of the themes are not the same everywhere
const ARROW_UP_ICON = `
    <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
        <path fill="currentColor" d="M8 1.5 13 7h-3v7.5H6V7H3z"/>
    </svg>
`;

const SITEMAP_ICON = `
    <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
        <path fill="none" stroke="currentColor" stroke-width="1.2"
              d="M8 4v3.5M3.5 12V7.5h9V12"/>
        <rect fill="currentColor" x="6" y="1" width="4" height="3"/>
        <rect fill="currentColor" x="1.5" y="12" width="4" height="3"/>
        <rect fill="currentColor" x="10.5" y="12" width="4" height="3"/>
    </svg>
`;

// the buttons are a screen affordance, they have no place in an export
function node_buttons(node, view) {
    if (view.exporting) {
        return '';
    }

    let buttons = '';

    // only the root of a drilled down chart has a level above it
    if (node.data.id === view.root_id && view.parent_id !== null) {
        buttons += `
            <button class="drillup"
                    data-drillup="${escape_html(view.parent_id)}"
                    title="${escape_html(view.drillup_label)}">
                ${ARROW_UP_ICON}
            </button>
        `;
    }

    if (node.data._directSubordinates) {
        buttons += `
            <button class="drilldown"
                    data-drilldown="${escape_html(node.data.id)}"
                    title="${escape_html(view.drilldown_label)}">
                ${SITEMAP_ICON}
            </button>
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

// browsers refuse to draw canvases beyond ~16'000 pixels per side - the
// area is limited as well, though in practice the memory of the canvas
// runs out first, at four bytes per pixel (80 megapixels are ~320 MiB)
const MAX_EXPORT_SIZE = 15000;
const MAX_EXPORT_AREA = 80 * 1000 * 1000;
// four pixels per pixel of the chart yields roughly 400 dpi
const EXPORT_SCALE = 4;
const EXPORT_MARGIN = 50;

/*
    Turns the bounds of the chart into the size of the exported image.

    The scale is a multiplier on the natural size, limited by what the
    browser is able to draw. Anything below 1 would shrink the chart into
    the image and cost the readability the natural size buys us, so such
    charts don't fit into a png at all - only the svg export can hold them.
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

/*
    Exports the visible nodes as an image.

    The chart is blown up to its natural size for the export, so the nodes
    end up as readable in the image as they are on screen - d3's own 'full'
    export fits the whole chart into the viewport first, which leaves large
    charts unreadable no matter the resolution.
*/
function export_image(chart, container, view) {
    const state = chart.getChartState();
    const nodes = state.root.descendants();

    // the chart uses the 'top' layout, where x is the center of a node
    const bounds = {
        left: d3.min(nodes, (node) => node.x - node.width / 2),
        right: d3.max(nodes, (node) => node.x + node.width / 2),
        top: d3.min(nodes, (node) => node.y),
        bottom: d3.max(nodes, (node) => node.y + node.height)
    };

    const size = export_dimensions(bounds);

    if (!size.fits) {
        set_message(container.dataset.exportErrorMessage);
        return;
    }
    set_message('');

    // the enlarged chart would push the page around, so it is clipped
    container.style.overflow = 'hidden';
    state.svg.attr('width', size.width).attr('height', size.height);
    state.centerG.attr('transform', 'translate(0,0)');
    state.chart.attr(
        'transform',
        `translate(${EXPORT_MARGIN - bounds.left},${EXPORT_MARGIN - bounds.top})`
    );

    // the export is serialized in a later tick, so the buttons stay away
    // until the image is loaded
    view.exporting = true;
    chart.restyleForeignObjectElements();

    chart.exportImg({
        scale: size.scale,
        onLoad: () => {
            view.exporting = false;
            container.style.overflow = '';
            chart.render().fit();
        }
    });
}

// the svg is serialized right away, so the buttons come back immediately
function export_svg(chart, view) {
    view.exporting = true;
    chart.restyleForeignObjectElements();
    chart.exportSvg();
    view.exporting = false;
    chart.restyleForeignObjectElements();
}

function init_topic_chart(container) {
    // what the chart currently shows: all nodes, drilled down to root_id
    const view = {
        nodes: [],
        root_id: null,
        // the node above the current root, null while the whole chart shows
        parent_id: null,
        exporting: false,
        drilldown_label: container.dataset.drilldownLabel || '',
        drillup_label: container.dataset.drillupLabel || ''
    };

    const chart = new d3.OrgChart()
        .container(container)
        .nodeWidth(() => 220)
        .nodeHeight(() => 90)
        .childrenMargin(() => 60)
        .siblingsMargin(() => 20)
        // the level is the depth of the deepest expanded node, so 1 shows
        // two levels: the root and its children
        .initialExpandLevel(1)
        .imageName(container.dataset.imageName || 'topic-chart')
        .nodeContent((node) => node_content(node, view));

    const draw = () => {
        const root = view.nodes.filter((node) => node.id === view.root_id)[0];
        const parent = root && view.nodes.filter(
            (node) => node.id === root.parentId
        )[0];

        // the topmost node is the whole chart, which has no drilled state
        view.parent_id = null;
        if (parent) {
            view.parent_id = parent.parentId ? parent.id : '';
        }

        chart.data(branch(view.nodes, view.root_id)).render().fit();

        document.querySelectorAll('[data-chart-action="reset"]').forEach(
            (button) => {
                button.hidden = !view.root_id;
            }
        );
    };

    const actions = {
        expand: () => chart.expandAll().fit(),
        collapse: () => chart.collapseAll().fit(),
        fit: () => chart.fit(),
        export: () => export_image(chart, container, view),
        // the svg keeps the nodes as html inside foreignObject elements,
        // which browsers render, but most vector editors do not
        'export-svg': () => export_svg(chart, view),
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
            // an empty target drills up to the whole chart
            view.root_id = down ? down.dataset.drilldown :
                up.dataset.drillup || null;
            draw();
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
    const container = document.querySelector('.topic-chart[data-url]');
    if (container) {
        init_topic_chart(container);
    }
});

// the nodes, the export math and the drill down are unit tested in tests/js
if (typeof module !== 'undefined') {
    module.exports = {
        export_dimensions: export_dimensions,
        node_content: node_content,
        branch: branch
    };
}
