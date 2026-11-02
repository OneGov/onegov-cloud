document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
});

document.addEventListener('htmx:afterSwap', function() {
    lucide.createIcons();
});

// Elements added with jQuery (e.g. uploaded images)
$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).each(function() {
        lucide.createIcons({root: this});
    });
});

