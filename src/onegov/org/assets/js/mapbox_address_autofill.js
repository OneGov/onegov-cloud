(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    const token = getMapboxToken();
    if (token) {
        mapboxsearch.config.accessToken = token;
        const autofillInstance = mapboxsearch.autofill({
            querySelector: '#hometown', // Apply only to the hometown field
            mapboxSearchBoxOptions: { // Options for the search box itself
                country: 'CH',
                language: 'de',
                types: 'place,region', // Prioritize cities and cantons
            }
        });

        if (autofillInstance) {
            autofillInstance.addEventListener('suggest', (event) => {
                if (event.detail && event.detail.suggestions) {
                    // Filter out results identified by 'feature_type' as 'address'.
                    // The Search Box API /suggest endpoint uses 'feature_type'.
                    event.detail.suggestions = event.detail.suggestions.filter(
                        suggestion => !(suggestion.feature_type && suggestion.feature_type === 'address')
                    );
                }
            });
        }
    }
})();
