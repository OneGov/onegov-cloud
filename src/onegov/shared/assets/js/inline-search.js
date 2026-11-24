// town6 clones the form into the off-canvas menu (duplicate ids), so match
// by attribute and scope lookups to the submitted form
$(document).on('submit', '[id="inline-search"]', function() {
    var form = $(this);

    form.find('input[name="search_query"]').val(JSON.stringify({
        'term': form.find('[id="search-term"]').val()
    }));

    return true;
});

// the reset button clears the search term but keeps any active filters
$(document).on('click', '[id="inline-search"] .reset-button', function(e) {
    e.preventDefault();
    var url = new URL(window.location.href);
    url.searchParams.delete('search');
    url.searchParams.delete('search_query');
    window.location = url.toString();
});
