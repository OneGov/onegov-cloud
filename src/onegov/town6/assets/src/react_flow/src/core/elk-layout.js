import ELK from 'elkjs/lib/elk.bundled.js';


const elk = new ELK();


export async function getElkLayout(
    nodes,
    edges,
    {
        direction = 'DOWN',
        layerSpacing = 90,
        layoutOptions = {},
        nodeSpacing = 48
    } = {}
) {
    const graph = await elk.layout({
        id: 'root',
        layoutOptions: {
            'elk.algorithm': 'layered',
            'elk.direction': direction,
            'elk.layered.spacing.nodeNodeBetweenLayers': `${layerSpacing}`,
            'elk.spacing.nodeNode': `${nodeSpacing}`,
            ...layoutOptions
        },
        children: nodes.map((node) => ({
            id: node.id,
            width: node.width,
            height: node.height
        })),
        edges: edges.map((edge) => ({
            id: edge.id,
            sources: [edge.source],
            targets: [edge.target]
        }))
    });

    return new Map((graph.children || []).map((node) => [
        node.id,
        {x: node.x, y: node.y}
    ]));
}
