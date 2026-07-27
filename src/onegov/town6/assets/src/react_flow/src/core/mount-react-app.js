import {createRoot} from 'react-dom/client';


export function mountReactApp({containerId, createApp, prepareContainer}) {
    const mount = () => {
        const container = document.getElementById(containerId);
        if (!container || container.dataset.mounted === 'true') {
            return;
        }

        container.dataset.mounted = 'true';
        prepareContainer?.(container);
        createRoot(container).render(createApp(container));
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mount, {once: true});
    } else {
        mount();
    }
}
