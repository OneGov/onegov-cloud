(function() {
    const accessToken = document.body.dataset.mapboxToken || false;
    if (!accessToken) {
        // console.warn('Mapbox access token not found.');
        return;
    }

    function generateUUIDv4() {
        return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
            (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
        );
    }
    const sessionToken = generateUUIDv4();

    // Debounce function to limit API calls
    function debounce(func, delay) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), delay);
        };
    }

    const autocompleteInputs = document.querySelectorAll('mapbox-address-autofill input[autocomplete]');

    autocompleteInputs.forEach(input => {
        const suggestionsContainer = document.createElement('ul');
        suggestionsContainer.classList.add('mapbox-suggestions');
        input.parentNode.insertBefore(suggestionsContainer, input.nextSibling);

        const fetchSuggestions = async function(event) {
            const query = event.target.value;

            if (query.length < 2) { // Minimum characters to trigger search
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
                return;
            }

            const autocompleteType = event.target.getAttribute('autocomplete');
            let apiTypes = [];
            switch (autocompleteType) {
                case 'address-level1': // LEAST_SPECIFIC (e.g., Canton for CH)
                    apiTypes = ['region'];
                    break;
                case 'address-level2': // MORE_SPECIFIC (e.g., City/Municipality for CH)
                    apiTypes = ['place'];
                    break;
                case 'address-level3': // MOST_SPECIFIC (e.g., District or less common)
                    apiTypes = ['district', 'place'];
                    break;
                case 'address-line1': // STREET_NUMBER and street name
                    apiTypes = ['address', 'street'];
                    break;
                default: // Fallback for other types if necessary
                    apiTypes = ['place', 'region', 'address'];
            }

            const params = new URLSearchParams({
                q: query,
                access_token: accessToken,
                session_token: sessionToken,
                language: document.documentElement.lang || 'de',
                country: 'ch', // Assuming CH, make dynamic if needed
                types: apiTypes.join(','),
                limit: 5
            });

            try {
                const response = await fetch(`https://api.mapbox.com/search/searchbox/v1/suggest?${params.toString()}`);
                if (!response.ok) {
                    // console.error('Mapbox API error:', response.status, await response.text());
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                const data = await response.json();
                console.log('Mapbox API response data:', data);
                suggestionsContainer.innerHTML = ''; // Clear previous

                if (data.suggestions && data.suggestions.length > 0) {
                    data.suggestions.forEach(suggestion => {
                        const li = document.createElement('li');
                        console.log('Mapbox suggestion:', suggestion);
                        li.textContent = suggestion.name; // 'name' should be appropriate for 'region' type
                        li.addEventListener('click', () => {
                            input.value = suggestion.name;
                            suggestionsContainer.innerHTML = '';
                            suggestionsContainer.style.display = 'none';
                        });
                        suggestionsContainer.appendChild(li);
                    });
                    suggestionsContainer.style.display = 'block';
                } else {
                    suggestionsContainer.style.display = 'none';
                }
            } catch (error) {
                // console.error('Error fetching Mapbox suggestions:', error);
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.style.display = 'none';
            }
        };

        input.addEventListener('input', debounce(fetchSuggestions, 300));

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(event) {
            if (!input.contains(event.target) && !suggestionsContainer.contains(event.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });

        // Hide suggestions on blur if not clicking on a suggestion item
        input.addEventListener('blur', function() {
            // Timeout to allow click event on suggestion to fire first
            setTimeout(() => {
                if (!suggestionsContainer.matches(':hover')) {
                     suggestionsContainer.style.display = 'none';
                }
            }, 150);
        }
    )});
})();
