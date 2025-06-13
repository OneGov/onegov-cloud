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

        console.log('bar')
        console.log(autofillInstance)
        if (autofillInstance && autofillInstance.searchBox) {
            console.log('fo')
            autofillInstance.searchBox.addEventListener('results', (event) => {
                if (event.detail && event.detail.results) {
                    console.log('event.detail.results')
                    // Filter out results identified as 'address' type.
                    event.detail.results = event.detail.results.filter(result =>
                        !(result.place_type && result.place_type.includes('address'))
                    );
                }
            });
        }
    }
})();
