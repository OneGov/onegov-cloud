const typeaheadInputs = document.getElementsByClassName("typeahead-standalone-field");
for (let index = 0; index < typeaheadInputs.length; index++) {
    const url = typeaheadInputs[index].dataset.url;
    typeahead({
        input: typeaheadInputs[index],
        minLenght: 2,
        preventSubmit: true,
        source: {
            remote: {
                url: url,
                wildcard: '%QUERY'
            }
        }
    });
}
