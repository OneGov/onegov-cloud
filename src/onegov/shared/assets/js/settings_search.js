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
            var title = setting.textContent.trim().toLocaleLowerCase();
            var visible = title.indexOf(query) !== -1;

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
}());
