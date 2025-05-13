(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    // mapboxsearch.config.accessToken = getMapboxToken();
    //
    mapboxsearch.autofill(
        accessToken: getMapboxToken(),
        options={
            country: 'ch',
            language: 'de',
            types: 'place,region', // Prioritize cities and cantons
            streets: false
        });

})();
