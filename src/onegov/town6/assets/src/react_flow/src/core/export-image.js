import {getNodesBounds, getViewportForBounds} from '@xyflow/react';
import {toBlob} from 'html-to-image';


export async function createFlowPng(
    viewport,
    nodes,
    {
        backgroundColor = '#fff',
        maxEdge = 8192,
        maxPixels = 32000000,
        padding = 64
    } = {}
) {
    if (!viewport || nodes.length === 0) {
        throw new Error('A viewport and at least one node are required');
    }

    await document.fonts?.ready;
    const bounds = getNodesBounds(nodes);
    const naturalWidth = bounds.width + 2 * padding;
    const naturalHeight = bounds.height + 2 * padding;
    const zoom = Math.min(
        1,
        maxEdge / naturalWidth,
        maxEdge / naturalHeight,
        Math.sqrt(maxPixels / (naturalWidth * naturalHeight))
    );
    const width = Math.max(1, Math.ceil(naturalWidth * zoom));
    const height = Math.max(1, Math.ceil(naturalHeight * zoom));
    const scaledPadding = Math.max(1, Math.round(padding * zoom));
    const exportViewport = getViewportForBounds(
        bounds,
        width,
        height,
        zoom,
        zoom,
        `${scaledPadding}px`
    );
    const blob = await toBlob(viewport, {
        backgroundColor,
        height,
        pixelRatio: 1,
        skipAutoScale: true,
        skipFonts: true,
        style: {
            height: `${height}px`,
            transform: `translate(${exportViewport.x}px, ` +
                `${exportViewport.y}px) scale(${exportViewport.zoom})`,
            transformOrigin: '0 0',
            width: `${width}px`
        },
        width
    });

    if (!blob) {
        throw new Error('PNG creation returned no data');
    }
    return blob;
}


export function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = filename;
    link.href = url;
    link.style.display = 'none';
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
