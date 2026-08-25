(function() {
    'use strict';

    var search = document.querySelector('[data-settings-search]');
    var noResults = document.querySelector('[data-settings-no-results]');

    if (!search || !noResults) {
        return;
    }

    var categories = Array.prototype.slice.call(
        document.querySelectorAll('.settings-category')
    );
    var settings = Array.prototype.slice.call(
        document.querySelectorAll('[data-settings-item]')
    );

    search.addEventListener('input', function() {
        var query = search.value.trim().toLocaleLowerCase();
        var visibleSettings = 0;

        settings.forEach(function(setting) {
            var title = setting.querySelector('[data-settings-title]');
            var fieldList = setting.querySelector('[data-settings-fields]');
            var fields = Array.prototype.slice.call(
                setting.querySelectorAll('[data-settings-field]')
            );
            var titleMatches = title.textContent
                .trim()
                .toLocaleLowerCase()
                .indexOf(query) !== -1;
            var visibleFields = 0;

            fields.forEach(function(field) {
                var fieldMatches = query !== '' && field.textContent
                    .trim()
                    .toLocaleLowerCase()
                    .indexOf(query) !== -1;

                field.hidden = !fieldMatches;
                visibleFields += fieldMatches ? 1 : 0;
            });

            fieldList.hidden = query === '' || visibleFields === 0;

            var visible = query === '' || titleMatches || visibleFields > 0;

            setting.hidden = !visible;
            visibleSettings += visible ? 1 : 0;
        });

        categories.forEach(function(category) {
            var visible = category.querySelector(
                '[data-settings-item]:not([hidden])'
            );
            category.hidden = !visible;
        });

        noResults.hidden = visibleSettings !== 0;
    });
})();
