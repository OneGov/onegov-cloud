(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    mapboxsearch.config.accessToken = getMapboxToken();
    mapboxsearch.autofill({
        country: 'ch'
    });
})();
