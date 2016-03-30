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

function asCrosshairMap(map, input) {
    // a crosshair map updates the input coordinates with the center of
    // the map as well as the zoom, whenever either changes

    map.on('move', function(e) {
        setCoordinates(input, mapToCoordinates(
            e.target.getCenter(), e.target.getZoom()
        ));
    });
}

var MapboxInput = function(input) {
    mapboxgl.accessToken = $('body').data('mapbox-token') || false;

    var coordinates = getCoordinates(input);

    // the default is seantis hq - as good a place as any
    var lat = coordinates.lat || 47.0517251;
    var lon = coordinates.lon || 8.3054817;
    var zoom = coordinates.zoom || 5;

    var el = $('<div class="map-wrapper">')
        .insertBefore(input.hide());

    // the height depends on the width using the golden ratio
    el.css('height', input.data('map-height') || $(el).width() / 1.618 + 'px');

    var map = new mapboxgl.Map({
        container: el[0],
        style: 'mapbox://styles/mapbox/streets-v8',
        center: [lon, lat],
        zoom: zoom
    });

    // hide the improve map link, it's not translated, looks ugly and doesn't
    // *have* to be included (unlike the copyright labels)
    map.on('load', function(e) {
        $(e.target._container).find('.mapbox-improve-map').remove();
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
