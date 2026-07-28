import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState
} from 'react';
import {
    Background,
    BackgroundVariant,
    Controls,
    Handle,
    MiniMap,
    Panel,
    Position,
    ReactFlow,
    ReactFlowProvider,
    useReactFlow
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {getElkLayout} from '../../core/elk-layout.js';
import {createFlowPng, downloadBlob} from '../../core/export-image.js';
import {useJsonResource} from '../../core/use-json-resource.js';

const NODE_WIDTH = 260;
const MIN_NODE_HEIGHT = 112;
const TITLE_LINE_HEIGHT = 20;
const LEAD_PREVIEW_EXTRA_HEIGHT = 16;
const TITLE_TEXT_WIDTH = NODE_WIDTH - 40;
const titleMeasureContext = document.createElement('canvas').getContext('2d');
const TreeContext = createContext({
    active: false,
    matchingNodeIds: new Set(),
    toggleBranch: () => {}
});

function getTextLineCount(text, font, textWidth) {
    const paragraphs = text.trim().split(/\r?\n/);
    if (!titleMeasureContext) {
        return paragraphs.reduce((total, paragraph) => (
            total + Math.max(1, Math.ceil(paragraph.length / 28))
        ), 0);
    }
    titleMeasureContext.font = font;
    const spaceWidth = titleMeasureContext.measureText(' ').width;
    return paragraphs.reduce((total, paragraph) => {
        let lineCount = 1;
        let lineWidth = 0;

        paragraph.trim().split(/\s+/).filter(Boolean).forEach((word) => {
            const wordWidth = titleMeasureContext.measureText(word).width;
            if (lineWidth > 0 &&
                lineWidth + spaceWidth + wordWidth <= textWidth) {
                lineWidth += spaceWidth + wordWidth;
                return;
            }
            if (lineWidth > 0) {
                lineCount += 1;
            }
            const wrappedLines = Math.max(
                1, Math.ceil(wordWidth / textWidth)
            );
            lineCount += wrappedLines - 1;
            lineWidth = wordWidth - (wrappedLines - 1) * textWidth;
        });
        return total + lineCount;
    }, 0);
}

function getTitleLineCount(title) {
    return Math.max(2, getTextLineCount(
        title, '700 15px sans-serif', TITLE_TEXT_WIDTH
    ));
}

function getNodeHeight(title, lead) {
    const extraTitleLines = getTitleLineCount(title) - 2;
    return MIN_NODE_HEIGHT +
        extraTitleLines * TITLE_LINE_HEIGHT +
        (lead ? LEAD_PREVIEW_EXTRA_HEIGHT : 0);
}

function getExportFilename(title) {
    const slug = title
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLocaleLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
    return `${slug || 'site'}-information-architecture.png`;
}

function flattenTree(
    root,
    collapsedNodeIds = new Set(),
    searchExpandedNodeIds = new Set()
) {
    const nodes = [];
    const edges = [];
    const parentById = new Map();

    function visit(node, parentId) {
        const {children, ...nodeData} = node;
        const lead = node.lead || '';
        const hasChildren = children.length > 0;
        const searchExpanded = searchExpandedNodeIds.has(node.id);
        const collapsed = hasChildren &&
            collapsedNodeIds.has(node.id) && !searchExpanded;
        const height = getNodeHeight(node.title, lead);
        nodes.push({
            id: node.id,
            type: 'page',
            data: {
                ...nodeData,
                lead,
                childCount: children.length,
                collapsed,
                searchExpanded,
                searchText: `${node.title} ${node.path} ${lead}`
                    .toLocaleLowerCase()
            },
            height,
            position: {x: 0, y: 0},
            style: node.url ? {pointerEvents: 'all'} : undefined,
            width: NODE_WIDTH
        });

        if (parentId) {
            parentById.set(node.id, parentId);
            edges.push({
                id: `${parentId}-${node.id}`,
                source: parentId,
                target: node.id,
                type: 'smoothstep'
            });
        }

        if (!collapsed) {
            children.forEach((child) => visit(child, node.id));
        }
    }

    visit(root, null);
    return {nodes, edges, parentById};
}

async function layoutElements(nodes, edges, direction) {
    const horizontal = direction === 'RIGHT';
    const positions = await getElkLayout(nodes, edges, {direction});

    return nodes.map((node) => ({
        ...node,
        data: {...node.data, direction},
        position: positions.get(node.id),
        sourcePosition: horizontal ? Position.Right : Position.Bottom,
        targetPosition: horizontal ? Position.Left : Position.Top
    }));
}

function PageNode({data}) {
    const tree = useContext(TreeContext);
    const horizontal = data.direction === 'RIGHT';
    const sourcePosition = horizontal ? Position.Right : Position.Bottom;
    const targetPosition = horizontal ? Position.Left : Position.Top;
    const restricted = data.access !== 'public';
    const searchMatch = tree.active && tree.matchingNodeIds.has(data.id);
    const hasChildren = data.childCount > 0;
    const classes = [
        'ia-node',
        `ia-node--${data.kind}`,
        hasChildren ? 'ia-node--has-children' : '',
        restricted ? 'ia-node--restricted' : '',
        data.published ? '' : 'ia-node--unpublished',
        searchMatch ? 'ia-node--search-match' : '',
        tree.active && !searchMatch ?
            'ia-node--search-dimmed' : ''
    ].filter(Boolean).join(' ');
    const kindLabel = data.labels[data.kind] || data.kind;
    const contents = (
        <>
            <span className="ia-node__meta">
                <span className="ia-node__kind">{kindLabel}</span>
                {restricted && (
                    <span
                        aria-label={data.labels.restricted}
                        className={
                            'ia-node__status ia-node__status--restricted'
                        }
                        role="img"
                        title={data.labels.restricted}
                    />
                )}
                {!data.published && (
                    <span
                        aria-label={data.labels.unpublished}
                        className={
                            'ia-node__status ia-node__status--unpublished'
                        }
                        role="img"
                        title={data.labels.unpublished}
                    />
                )}
            </span>
            <span className="ia-node__title">{data.title}</span>
            {data.lead && (
                <span className="ia-node__lead">{data.lead}</span>
            )}
        </>
    );

    return (
        <>
            <Handle type="target" position={targetPosition}/>
            {data.url ? (
                <a
                    aria-label={`${data.labels.open_page}: ${data.title}`}
                    className={classes}
                    href={data.url}
                    onMouseDown={(event) => event.stopPropagation()}
                    rel="noreferrer"
                    target="_blank"
                >
                    {contents}
                    <span aria-hidden="true" className="ia-node__link-icon">
                        ↗
                    </span>
                </a>
            ) : (
                <div className={classes}>
                    {contents}
                </div>
            )}
            <Handle type="source" position={sourcePosition}/>
            {hasChildren && (
                <button
                    aria-expanded={!data.collapsed}
                    aria-label={`${data.collapsed ?
                        data.labels.expand_branch :
                        data.labels.collapse_branch}: ${data.path}`}
                    className={data.url ?
                        'ia-node__toggle ia-node__toggle--with-link ' +
                            'nodrag nopan' :
                        'ia-node__toggle nodrag nopan'}
                    disabled={data.searchExpanded}
                    onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        tree.toggleBranch(data.id);
                    }}
                    onPointerDown={(event) => event.stopPropagation()}
                    title={data.collapsed ?
                        data.labels.expand_branch :
                        data.labels.collapse_branch}
                    type="button"
                >
                    <span aria-hidden="true">
                        {data.collapsed ? '+' : '−'}
                    </span>
                </button>
            )}
        </>
    );
}

const nodeTypes = {page: PageNode};

function LayoutButton({active, direction, icon, label, onChange}) {
    return (
        <button
            aria-label={label}
            aria-pressed={active}
            className="ia-tree__layout-button"
            onClick={() => onChange(direction)}
            title={label}
            type="button"
        >
            <span aria-hidden="true" className="ia-tree__layout-icon">
                {icon}
            </span>
            <span className="ia-tree__layout-label">{label}</span>
        </button>
    );
}

function PageSearch({labels, matchCount, onChange, query, totalCount}) {
    const active = query.trim().length > 0;
    const input = useRef(null);
    const clear = () => {
        onChange('');
        window.requestAnimationFrame(() => input.current?.focus());
    };

    return (
        <form
            className="ia-tree__search"
            onSubmit={(event) => event.preventDefault()}
            role="search"
        >
            <i aria-hidden="true" className="fas fa-search"/>
            <input
                aria-label={labels.search}
                className="ia-tree__search-input"
                onChange={(event) => onChange(event.target.value)}
                onKeyDown={(event) => {
                    if (event.key === 'Escape') {
                        event.preventDefault();
                        clear();
                    }
                }}
                placeholder={labels.search}
                ref={input}
                spellCheck={false}
                type="search"
                value={query}
            />
            {active && (
                <output
                    aria-label={labels.search_results}
                    aria-live="polite"
                    className="ia-tree__search-count"
                >
                    {matchCount}/{totalCount}
                </output>
            )}
            {query && (
                <button
                    aria-label={labels.clear_search}
                    className="ia-tree__search-clear"
                    onClick={clear}
                    title={labels.clear_search}
                    type="button"
                >
                    <span aria-hidden="true">×</span>
                </button>
            )}
        </form>
    );
}

function PageTree({payload}) {
    const fullGraph = useMemo(
        () => flattenTree(payload.tree),
        [payload.tree]
    );
    const canvas = useRef(null);
    const [collapsedNodeIds, setCollapsedNodeIds] = useState(
        () => new Set(['route-news'])
    );
    const [direction, setDirection] = useState('DOWN');
    const [nodes, setNodes] = useState([]);
    const [query, setQuery] = useState('');
    const [layouting, setLayouting] = useState(true);
    const [layoutError, setLayoutError] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [exportError, setExportError] = useState(false);
    const {fitView, getNodes} = useReactFlow();
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const matchingNodeIds = useMemo(() => {
        if (!normalizedQuery) {
            return new Set();
        }
        return new Set(
            fullGraph.nodes
                .filter((node) => node.data.searchText.includes(
                    normalizedQuery
                ))
                .map((node) => node.id)
        );
    }, [fullGraph.nodes, normalizedQuery]);
    const searchAncestorIds = useMemo(() => {
        const ancestors = new Set();
        matchingNodeIds.forEach((nodeId) => {
            let parentId = fullGraph.parentById.get(nodeId);
            while (parentId) {
                ancestors.add(parentId);
                parentId = fullGraph.parentById.get(parentId);
            }
        });
        return ancestors;
    }, [fullGraph.parentById, matchingNodeIds]);
    const forcedExpansionKey = useMemo(() => (
        [...collapsedNodeIds]
            .filter((nodeId) => searchAncestorIds.has(nodeId))
            .sort()
            .join('\u0000')
    ), [collapsedNodeIds, searchAncestorIds]);
    const graph = useMemo(() => flattenTree(
        payload.tree,
        collapsedNodeIds,
        new Set(forcedExpansionKey ? forcedExpansionKey.split('\u0000') : [])
    ), [collapsedNodeIds, forcedExpansionKey, payload.tree]);
    const searchActive = Boolean(normalizedQuery);
    const toggleBranch = useCallback((nodeId) => {
        setLayouting(true);
        setCollapsedNodeIds((current) => {
            const next = new Set(current);
            if (next.has(nodeId)) {
                next.delete(nodeId);
            } else {
                next.add(nodeId);
            }
            return next;
        });
    }, []);
    const treeContext = useMemo(() => ({
        active: searchActive,
        matchingNodeIds,
        toggleBranch
    }), [matchingNodeIds, searchActive, toggleBranch]);
    const getMinimapNodeColor = useCallback((node) => {
        if (searchActive) {
            return matchingNodeIds.has(node.id) ? '#d97706' : '#d6dde6';
        }
        return node.data.kind === 'homepage' ? '#1779ba' : '#9aa8b8';
    }, [matchingNodeIds, searchActive]);
    const changeDirection = useCallback((nextDirection) => {
        if (nextDirection === direction) {
            return;
        }
        setLayouting(true);
        setDirection(nextDirection);
    }, [direction]);
    const exportImage = useCallback(async () => {
        const viewport = canvas.current?.querySelector(
            '.react-flow__viewport'
        );
        const exportNodes = getNodes();
        if (
            !viewport || layouting || layoutError || exporting ||
            exportNodes.length === 0
        ) {
            return;
        }

        setExporting(true);
        setExportError(false);
        try {
            const blob = await createFlowPng(viewport, exportNodes, {
                backgroundColor: '#f7f9fc'
            });
            downloadBlob(blob, getExportFilename(payload.tree.title));
        } catch {
            setExportError(true);
        } finally {
            setExporting(false);
        }
    }, [
        exporting,
        getNodes,
        layoutError,
        layouting,
        payload.tree.title
    ]);

    useEffect(() => {
        let active = true;
        setLayouting(true);
        setLayoutError(false);

        layoutElements(graph.nodes, graph.edges, direction)
            .then((layoutedNodes) => {
                if (!active) {
                    return;
                }
                setNodes(layoutedNodes.map((node) => ({
                    ...node,
                    data: {...node.data, labels: payload.labels}
                })));
                setLayouting(false);
            })
            .catch(() => {
                if (active) {
                    setLayoutError(true);
                    setLayouting(false);
                }
            });

        return () => {
            active = false;
        };
    }, [direction, graph, payload.labels]);

    useEffect(() => {
        if (layouting || layoutError || nodes.length === 0) {
            return undefined;
        }
        const hasMatches = Boolean(
            normalizedQuery && matchingNodeIds.size > 0
        );
        const targetIds = hasMatches ?
            [...matchingNodeIds] : nodes.map((node) => node.id);
        let frame;
        const timeout = window.setTimeout(() => {
            frame = window.requestAnimationFrame(() => {
                fitView({
                    duration: 250,
                    maxZoom: hasMatches ? 1.25 : 1.8,
                    nodes: targetIds.map((id) => ({id})),
                    padding: hasMatches ? .5 : .16
                });
            });
        }, 180);
        return () => {
            window.clearTimeout(timeout);
            if (frame !== undefined) {
                window.cancelAnimationFrame(frame);
            }
        };
    }, [
        fitView,
        layoutError,
        layouting,
        matchingNodeIds,
        nodes,
        normalizedQuery
    ]);

    return (
        <div className={searchActive ?
            'ia-tree ia-tree--search-active' : 'ia-tree'}>
            <div className="ia-tree__toolbar">
                <div className="ia-tree__toolbar-primary">
                    <span className="ia-tree__summary">
                        {payload.summary}
                    </span>
                    <div className="ia-tree__layout-controls">
                        <LayoutButton
                            active={direction === 'DOWN'}
                            direction="DOWN"
                            icon="↓"
                            label={payload.labels.vertical}
                            onChange={changeDirection}
                        />
                        <LayoutButton
                            active={direction === 'RIGHT'}
                            direction="RIGHT"
                            icon="→"
                            label={payload.labels.horizontal}
                            onChange={changeDirection}
                        />
                    </div>
                </div>
                <PageSearch
                    labels={payload.labels}
                    matchCount={matchingNodeIds.size}
                    onChange={setQuery}
                    query={query}
                    totalCount={fullGraph.nodes.length}
                />
                <button
                    aria-busy={exporting}
                    className="ia-tree__export-button"
                    disabled={
                        exporting || layouting || layoutError ||
                        nodes.length === 0
                    }
                    onClick={exportImage}
                    title={payload.labels.export_image}
                    type="button"
                >
                    <i
                        aria-hidden="true"
                        className={exporting ?
                            'fas fa-spinner fa-spin' : 'fas fa-image'}
                    />
                    <span>
                        {exporting ? payload.labels.exporting_image :
                            payload.labels.export_image}
                    </span>
                </button>
                {exportError && (
                    <span className="ia-tree__export-error" role="alert">
                        {payload.labels.export_error}
                    </span>
                )}
            </div>
            <div className="ia-tree__canvas" ref={canvas}>
                <TreeContext.Provider value={treeContext}>
                    <ReactFlow
                        edges={graph.edges}
                        edgesFocusable={false}
                        elementsSelectable={false}
                        maxZoom={1.8}
                        minZoom={.04}
                        nodeTypes={nodeTypes}
                        nodes={nodes}
                        nodesConnectable={false}
                        nodesDraggable={false}
                        nodesFocusable={false}
                        panOnScroll
                        zoomOnDoubleClick={false}
                    >
                    <Background
                        color="#cdd5df"
                        gap={20}
                        size={1.2}
                        variant={BackgroundVariant.Dots}
                    />
                    <Controls showInteractive={false}/>
                    <MiniMap
                        maskColor="rgba(247, 249, 252, .72)"
                        nodeColor={getMinimapNodeColor}
                        pannable
                        zoomable
                    />
                    {(layouting || layoutError) && (
                        <Panel position="bottom-center">
                            <div
                                aria-live="polite"
                                className="ia-tree__layout-status"
                                role="status"
                            >
                                {layouting && (
                                    <i
                                        aria-hidden="true"
                                        className="fas fa-spinner fa-spin"
                                    />
                                )}
                                <span>
                                    {layoutError ? payload.labels.error :
                                        payload.labels.loading}
                                </span>
                            </div>
                        </Panel>
                    )}
                    </ReactFlow>
                </TreeContext.Provider>
            </div>
        </div>
    );
}

function Status({label, loading}) {
    return (
        <div
            aria-live="polite"
            className="information-architecture-status"
            role="status"
        >
            {loading && (
                <i aria-hidden="true" className="fas fa-spinner fa-spin"/>
            )}
            <span>{label}</span>
        </div>
    );
}

export function InformationArchitectureApp({
    endpoint,
    errorLabel,
    loadingLabel
}) {
    const {data: payload, error, loading} = useJsonResource(endpoint);

    if (error) {
        return <Status label={errorLabel} loading={false}/>;
    }
    if (loading) {
        return <Status label={loadingLabel} loading/>;
    }
    return (
        <ReactFlowProvider>
            <PageTree payload={payload}/>
        </ReactFlowProvider>
    );
}
