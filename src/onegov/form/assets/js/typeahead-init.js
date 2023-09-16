const typeaheadInputs = document.getElementsByClassName("typeaheadstd");
for (let index = 0; index < typeaheadInputs.length; index++) {
    typeahead({
        input: typeaheadInputs[index],
        minLenght: 2,
        preventSubmit: true,
        source: {
            // local: ['Hans', 'Dampf', 'Hans Dampf']
            remote: {
              // url: 'https://remoteapi.com/%QUERY', // OR `url: () => 'https://remoteapi.com/%QUERY',`
              // wildcard: '%QUERY',
            },
        }
    })
}
