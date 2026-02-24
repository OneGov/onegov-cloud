(function() {
    if (!window.mapboxsearch || !document.body.dataset.mapboxToken) {
        if (!window.mapboxsearch) {
            console.warn('Mapbox Search JS SDK (mapboxsearch) not found.');
        }
        if (!document.body.dataset.mapboxToken) {
            console.warn('Mapbox token not found in document.body.dataset.mapboxToken.');
        }
        return;
    }
    const token = document.body.dataset.mapboxToken;

    // Select input fields based on standard autocomplete attributes
    // that correspond to MapboxPlaceDetail enum values.
    const inputs = document.querySelectorAll(
        'input[autocomplete^="address-line"], input[autocomplete^="address-level"]'
    );

    inputs.forEach((inputElement) => {
        const autocompleteValue = inputElement.getAttribute('autocomplete');

        const autocompleteToTypes = {
            'address-line1': 'address', // Street number and name
            'address-line2': 'address', // Apartment, suite, floor, etc. (part of address)
            'address-level1': 'region,country', // State, Province, Territory
            'address-level2': 'place,locality', // City, Municipality
            'address-level3': 'district', // County or another district level
            'default': 'address,place,postcode,region,country' // Generic fallback
        };

        const types = autocompleteToTypes[autocompleteValue] || autocompleteToTypes['default'];

        const searchBoxElement = new mapboxsearch.MapboxSearchBox();
        searchBoxElement.accessToken = token;
        searchBoxElement.options = {
            country: 'CH',
            language: 'de',
            types: types,
        };

        searchBoxElement.style.paddingTop = '0.5em!important';
        searchBoxElement.style.paddingBottom = '0.5em!important';

        // Hide the original input element because the searchBoxElement is the one capbable of search
        // We use the stategy where we basically overlayed on that
        inputElement.style.display = 'none';

        // Insert the MapboxSearchBox element after the original input
        if (inputElement.parentElement) {
            inputElement.parentElement.insertBefore(searchBoxElement, inputElement.nextSibling);
        }
        // Preserve the initial value from the original input, after DOM insertion
        searchBoxElement.value = inputElement.value;


        // Sync the value from the MapboxSearchBox back to the hidden original input
        searchBoxElement.addEventListener('retrieve', (event) => {
            const selectedItem = event.detail;

            if (selectedItem && selectedItem.features && selectedItem.features.length > 0) {
                const feature = selectedItem.features[0];
                const placeName = (feature.properties && feature.properties.name) || '';

                if (placeName) {
                    inputElement.value = placeName;
                    searchBoxElement.value = placeName;
                }
            }
        });

        // Handle manual edits in the search box
        searchBoxElement.addEventListener('input', () => {
            // Sync the manually entered value back to the original input
            if (searchBoxElement.value) {
                inputElement.value = searchBoxElement.value;
            }
        });


    });
})();
