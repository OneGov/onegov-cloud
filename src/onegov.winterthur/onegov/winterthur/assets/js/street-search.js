var Street = function(element) {
    return {
        name: element.getAttribute('data-street'),
        letter: element.getAttribute('data-letter')
    };
};

var getStreets = function(elements) {
    var streets = {};

    for (var i = 0; i < elements.length; i++) {
        var street = new Street(elements[i]);
        streets[street.name] = street;
    }

    return streets;
};

var lowercaseText = function(text) {
    return text.toLowerCase();
};

var normalizeUmlauts = function(text) {
    return text.replace(/ü|ö|ä/g, function(match) {
        switch (match) {
            case 'ö':
                return 'o';
            case 'ä':
                return 'a';
            case 'ü':
                return 'u';
            default:
                return match;
        }
    });
};

var dashesToSpace = function(text) {
    return text.replace('-', ' ');
};

var streetSuffixExpression = new RegExp([
    'acker',
    'allee',
    'berg',
    'büel',
    'egg',
    'gasse',
    'grund',
    'hof',
    'platz',
    'strasse',
    'tal',
    'weg',
    'weid',
    'wies'
].join('|'), 'g');

var tokenizeStreets = function(text) {
    return text.replace(streetSuffixExpression, function(match) {
        return ' ' + match;
    });
};

var streetsSearch = function() {
    var selector = '[data-street]';
    var streets = getStreets(document.querySelectorAll(selector));
    var names = Object.keys(streets);

    Wade.config.processors = [
        lowercaseText,
        dashesToSpace,
        tokenizeStreets,
        normalizeUmlauts
    ];

    var search = Wade(names);

    return function(term) {
        return search(term)
            .filter(function(result) {
                return streets[names[result.index]].name.score(term) >= 0.25;
            })
            .map(function(result) {
                return streets[names[result.index]];
            });
    };
};

var setStylesheet = function(id, stylesheet) {
    var sheet = document.body.querySelector('#' + id);
    var isNew = true;

    if (sheet) {
        isNew = false;
    } else {
        sheet = document.createElement('style');
    }

    sheet.setAttribute('id', id);
    sheet.innerHTML = stylesheet;

    if (isNew) {
        document.body.appendChild(sheet);
    }
};

var showStreets = function(streets) {
    var letters = new Set();
    streets.forEach(function(street) {
        letters.add(street.letter);
    });

    var noResults = document.querySelector('[data-no-results]');
    noResults.style.display = streets.length === 0 && 'block' || 'none';

    var styles = [];

    styles.push('[data-letter] { display: none; }');
    letters.forEach(function(letter) {
        styles.push('[data-letter="' + letter + '"] { display: block; }');
    });

    styles.push('[data-street] { display: none; }');
    streets.forEach(function(street) {
        styles.push('[data-street="' + street.name + '"] { display: list-item; }');
    });

    setStylesheet('streets', styles.join('\n'));
};

var resetSearch = function() {
    setStylesheet('streets', '');

    var noResults = document.querySelector('[data-no-results]');
    noResults.style.display = 'none';
};

var initStreetSearch = function(input) {
    var search = streetsSearch();
    var handle_keypress = _.debounce(function(e) {
        var term = e.target.value.trim();

        if (term === '') {
            resetSearch();
        } else {
            showStreets(search(term));
        }
    }, 250);

    input.addEventListener('input', handle_keypress);
};

document.addEventListener('DOMContentLoaded', function() {
    var elements = document.querySelectorAll('[data-street-search]');

    // forEach and the like do not work on IE (as this is not an array)
    for (var i = 0; i < elements.length; i++) {
        initStreetSearch(elements[i]);
    }
});
