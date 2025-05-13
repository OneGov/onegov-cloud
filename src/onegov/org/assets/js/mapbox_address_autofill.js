(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    mapboxsearch.config.accessToken = getMapboxToken();
    mapboxsearch.autofill({
        options: {
            country: 'CH',
            language: 'de',
            types: 'place,region', // Prioritize cities and cantons
        }
    });
})();
