// town6 clones the form into the off-canvas menu (duplicate ids), so match
// by attribute and scope lookups to the submitted form
$(document).on('submit', '[id="inline-search"]', function() {
    var form = $(this);
    var term = form.find('[id="search-term"]').val();

    // an empty term resets the search: go to the unfiltered directory
    // instead of submitting an empty search_query
    if (!term || !term.trim()) {
        window.location = this.action.split('?')[0];
        return false;
    }

    form.find('input[name="search_query"]').val(JSON.stringify({
        'term': term
    }));

    return true;
});
