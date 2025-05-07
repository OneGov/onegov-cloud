(function() {
    const getMapboxTokenForAutofill = () => document.body.dataset.mapboxToken || false;
    mapboxsearch.config.accessToken = getMapboxTokenForAutofill();
    mapboxsearch.autofill({
        options: {
          country: 'ch'
        }
    });
})();
