import {mountReactApp} from '../core/mount-react-app.js';
import {
    InformationArchitectureApp
} from '../views/information_architecture/app.jsx';
import '../views/information_architecture/styles.css';


mountReactApp({
    containerId: 'information-architecture-tree',
    createApp: (container) => (
        <InformationArchitectureApp
            endpoint={container.dataset.url}
            errorLabel={container.dataset.errorLabel}
            loadingLabel={container.dataset.loadingLabel}
        />
    ),
    prepareContainer: (container) => {
        const accent = document.body.dataset.defaultMarkerColor;
        if (accent) {
            container.style.setProperty('--ia-accent', accent);
        }
    }
});
