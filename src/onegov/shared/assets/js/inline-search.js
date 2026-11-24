// town6 clones the form into the off-canvas menu (duplicate ids), so match
// by attribute and scope lookups to the submitted form
$(document).on('submit', '[id="inline-search"]', function() {
    var form = $(this);

    form.find('input[name="search_query"]').val(JSON.stringify({
        'term': form.find('[id="search-term"]').val()
    }));

    return true;
});

// the reset button clears the search and returns to the unfiltered directory
$(document).on('click', '[id="inline-search"] .reset-button', function(e) {
    e.preventDefault();
    window.location = $(this).closest('form')[0].action.split('?')[0];
});
