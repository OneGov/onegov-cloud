(function() {
    function initializeMapboxAutofill() {
        const getMapboxToken = () => document.body.dataset.mapboxToken || false;
        const token = getMapboxToken();

        if (!token) {
            console.warn('Mapbox access token not found in document.body.dataset.mapboxToken. Autofill will not be initialized.');
            return;
        }

        if (typeof mapboxsearch !== 'undefined' && mapboxsearch.config && mapboxsearch.autofill) {
            mapboxsearch.config.accessToken = token;
            mapboxsearch.autofill({
                options: {
                    country: 'ch' // Keep existing country configuration
                }
            });
        } else {
            console.warn('Mapbox Search JS (mapboxsearch object or its properties) not available. Autofill initialization skipped.');
        }
    }

    // Wait for the main Mapbox Search JS script (assumed to have id="search-js") to load.
    const mapboxCoreScript = document.getElementById('search-js');
    if (mapboxCoreScript) {
        // If mapboxsearch is already defined, the script has likely already loaded.
        if (typeof mapboxsearch !== 'undefined') {
            initializeMapboxAutofill();
        } else {
            mapboxCoreScript.addEventListener('load', initializeMapboxAutofill);
        }
    } else {
        // Fallback: If the specific script tag isn't found,
        // try initializing if mapboxsearch is already global,
        // or wait for DOMContentLoaded and try again.
        if (typeof mapboxsearch !== 'undefined') {
            initializeMapboxAutofill();
        } else {
            document.addEventListener('DOMContentLoaded', initializeMapboxAutofill);
        }
    }
})();
