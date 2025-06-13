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
                filterResults: (results) => {
                    if (!results) {
                        return [];
                    }
                    // Filter out results identified as 'address' type.
                    // This complements the server-side 'types' filter to ensure
                    // street-level results are not shown.
                    return results.filter(result =>
                        !(result.place_type && result.place_type.includes('address'))
                    );
                }
            }
        });
    }
})();
