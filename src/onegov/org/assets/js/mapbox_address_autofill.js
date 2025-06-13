(function() {
    const getMapboxToken = () => document.body.dataset.mapboxToken || false;
    const token = getMapboxToken();
    if (!token) return;

    // instantiate a <mapbox-search-box> element using the MapboxSearchBox class
    const searchBoxElement = new mapboxsearch.MapboxSearchBox()

    searchBoxElement.accessToken = token; 
    searchBoxElement.options = {
            country: 'CH',
            language: 'de',
            types: 'place,region', // Prioritize cities and cantons
    }
    console.log(searchBoxElement);

    // append <mapbox-search-box> to the document
    document.querySelector('#hometown').appendChild(searchBoxElement);

})();

