function getCoordinates(input) {
    return JSON.parse(window.atob(input.attr('value')));
}

function setCoordinates(input, coordinates) {
    return input.attr('value', window.btoa(JSON.stringify(coordinates)));
}

function mapToCoordinates(position, zoom) {
    return {
        'lat': position.lat,
        'lon': position.lng,
        'zoom': zoom
    };
}

function coordinatesToMap(coordinates) {
    return {'lat': coordinates.lat, 'lng': coordinates.lon};
}

function asCrosshairMap(map, input) {
    // a crosshair map updates the input coordinates with the center of
    // the map as well as the zoom, whenever either changes

    map.on('move', function(e) {
        setCoordinates(input, mapToCoordinates(
            e.target.getCenter(), e.target.getZoom()
        ));
    });
}

function getMapboxToken() {
    return $('body').data('mapbox-token') || false;
}

function getTiles() {
    var url = 'https://api.mapbox.com/v4/mapbox.streets/{z}/{x}/{y}';
    url += (L.Browser.retina ? '@2x.png' : '.png');
    url += '?access_token=' + getMapboxToken();

    return L.tileLayer(url, {
        attribution: '© <a href="https://www.mapbox.com/map-feedback/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    });
}

var MapboxInput = function(input) {
    var coordinates = getCoordinates(input);

    // the default is seantis hq - as good a place as any
    var lat = coordinates.lat || 47.0517251;
    var lon = coordinates.lon || 8.3054817;
    var zoom = coordinates.zoom || 5;

    input.hide();

    var wrapper = $('<div class="map-wrapper">')
        .insertAfter(input.closest('label'));

    var el = $('<div class="map">')
        .appendTo(wrapper);

    // the height depends on the width using the golden ratio
    el.css('height', input.data('map-height') || $(el).width() / 1.618 + 'px');

    var map = L.map(el[0])
        .addLayer(getTiles())
        .setView([lat, lon], zoom);

    map.on('load', function() {
        var container = $(map._container);

        // buttons inside the map lead to form-submit if not prevented form it
        container.find('button').on('click', function(e) {
            e.preventDefault();
        });
    });

    switch (input.data('map-type')) {
        case 'crosshair':
            asCrosshairMap(map, input);
            break;
        default:
            break;
    }
};

jQuery.fn.mapboxInput = function() {
    return this.each(function() {
        MapboxInput($(this));
    });
};

$(document).ready(function() {
    $('input.coordinates').mapboxInput();
});
