(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    mapboxsearch.config.accessToken = getMapboxToken();
    mapboxsearch.autofill({
        querySelector: '#hometown',
        mapboxSearchBoxOptions: {
            country: 'CH',
            language: 'de',
            types: 'place,region', // Prioritize cities and cantons
        }
    });
})();
