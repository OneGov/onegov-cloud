document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
});

document.addEventListener('htmx:afterSwap', function() {
    lucide.createIcons();
});

