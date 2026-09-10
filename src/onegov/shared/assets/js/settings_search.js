(function() {
    'use strict';

    var search = document.querySelector('[data-settings-search]');
    var dropdown = document.querySelector('[data-settings-search-results]');
    var noResults = document.querySelector('[data-settings-no-results]');

    if (!search || !dropdown || !noResults) {
        return;
    }

    var results = Array.prototype.slice.call(
        document.querySelectorAll('[data-settings-search-result]')
    );

    var closeDropdown = function() {
        dropdown.hidden = true;
        search.setAttribute('aria-expanded', 'false');
    };

    var updateResults = function() {
        var query = search.value.trim().toLocaleLowerCase();
        var visibleResults = 0;

        if (query === '') {
            closeDropdown();
            return;
        }

        results.forEach(function(result) {
            var searchText = result.getAttribute(
                'data-settings-search-text'
            ).toLocaleLowerCase();
            var visible = searchText.indexOf(query) !== -1;

            result.hidden = !visible;
            visibleResults += visible ? 1 : 0;
        });

        noResults.hidden = visibleResults !== 0;
        dropdown.hidden = false;
        search.setAttribute('aria-expanded', 'true');
    };

    search.addEventListener('input', updateResults);
    search.addEventListener('focus', updateResults);
    search.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeDropdown();
        }
    });
    document.addEventListener('click', function(event) {
        if (!search.parentElement.contains(event.target)) {
            closeDropdown();
        }
    });
})();
