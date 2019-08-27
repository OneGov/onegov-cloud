/*
    Click tracking for Google Analytics.

    Anything related to click tracking is created here, even though it might
    be more natural to implement in other places. The reason for this is that
    we want this to be in one place, since it is going to be in flux at least
    in the beginning.
*/

var trackedElements = function() {

    // all tracked elements must have a 'href' attribute at this point, since
    // we are currently asked to enable link tracking through link manipulation
    var definitions = [];

    // track donation links in the footer
    definitions.push({
        'targets': $('.donate-link[href]'),
        'params': {
            'utm_source': 'spendenLink',
            'utm_medium': 'spendenLinkFooter',
            'utm_campaign': 'feriennet'
        }
    });

    // track menu items which contain 'spende' or 'dons'
    definitions.push({
        'targets': $('.top-bar-section a:contains("Dons")[href], .top-bar-section a:contains("Spende")[href]'),
        'params': {
            'utm_source': 'spendenLink',
            'utm_medium': 'spendenLinkMenu',
            'utm_campaign': 'feriennet'
        }
    });

    return definitions;
};

var trackClicks = function() {
    trackedElements().forEach(function(definition) {
        definition.targets.toArray().forEach(function(target) {
            var url = new Url($(target).attr('href'));

            Object.keys(definition.params).forEach(function(key) {
                url.query[key] = definition.params[key];
            });

            $(target).attr('href', url.toString());
        });
    });
};

$(document).ready(trackClicks);
