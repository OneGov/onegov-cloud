(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    const token = getMapboxToken();
    if (token) {
        mapboxsearch.config.accessToken = token;
        mapboxsearch.autofill({
            querySelector: '#hometown', // Apply only to the hometown field
            mapboxSearchBoxOptions: { // Options for the search box itself
                country: 'CH',
                language: 'de',
                types: 'place,region', // Prioritize cities and cantons
            }
        });
    }
})();
