(function($) {
    $(document).ready(function() {
        $('.sortable-multi-checkbox').each(function() {
            Sortable.create(this);
        });
    });
})(jQuery);
