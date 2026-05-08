$(document).ready(function() {
    $('#inline-search').on('submit', function() {
        var query = {
            'term': $('#search-term').val()
        };

        $('input[name="search_query"]').val(JSON.stringify(query));

        return true;
    });
});
