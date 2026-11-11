$(document).ready(function() {
    var closedForPrint = $();
    var closedSections = '.page-text details.page-section:not([open])';

    var revealHashTarget = function() {
        var id;
        try {
            id = decodeURIComponent(window.location.hash.slice(1));
        } catch (_error) {
            return;
        }

        var target = document.getElementById(id);
        if (!target) {
            return;
        }

        var sections = $(target).parents(closedSections);
        if (sections.length) {
            sections.prop('open', true);
            target.scrollIntoView();
        }
    };

    revealHashTarget();
    $(window).on('hashchange', revealHashTarget);

    $(window).on('beforeprint', function() {
        var sections = $(closedSections);
        closedForPrint = closedForPrint.add(sections);
        sections.prop('open', true);
    }).on('afterprint', function() {
        closedForPrint.prop('open', false);
        closedForPrint = $();
    });
});
