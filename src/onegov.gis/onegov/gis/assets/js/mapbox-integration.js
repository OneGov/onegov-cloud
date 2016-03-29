function utf8_to_b64(str) {
    return window.btoa(escape(encodeURIComponent(str)));
}

function b64_to_utf8(str) {
    return decodeURIComponent(unescape(window.atob(str)));
}

function getCoordinates(input) {
    return JSON.parse(b64_to_utf8(input.val()));
}

function setCoordinates(input, coordinates) {
    return input.val(utf8_to_b64(JSON.stringify(coordinates)));
}

var MapboxInput = function(input) {
    mapboxgl.accessToken = $('body').data('mapbox-token') || false;

    var coordinates = getCoordinates(input);

    // the default is seantis hq - as good a place as any
    var lat = coordinates.lat || 47.0517251;
    var lon = coordinates.lon || 8.3054817;
    var zoom = coordinates.zoom || 5;

    var el = $('<div class="map-wrapper">')
        .css('min-height', '200px')
        .insertBefore(input.hide());

    var map = new mapboxgl.Map({
        container: el[0],
        style: 'mapbox://styles/mapbox/streets-v8',
        center: [lon, lat],
        zoom: zoom
    });
};

jQuery.fn.mapboxInput = function() {
    return this.each(function() {
        MapboxInput($(this));
    });
};

$(document).ready(function() {
    $('input.coordinates').mapboxInput();
});
