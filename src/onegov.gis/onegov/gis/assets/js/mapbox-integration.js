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

function asPointMap(map, input) {
    // a map where we can set (or remove) a single point

    var container = $(map._container).find('.mapboxgl-ctrl-top-right');
    var group = $('<div class="mapboxgl-ctrl-group mapboxgl-ctrl">');
    var ctrl = $('<button class="mapboxgl-ctrl-icon mapboxgl-ctrl-add-point">');

    ctrl.appendTo(group.appendTo(container));

    var isDragging, isCursorOverPoint;
    var canvas = map.getCanvasContainer();
    var geojson = {};

    var initPoint = function() {
        var coordinates = getCoordinates(input);
        var hasPoint = (coordinates.lat && coordinates.lon) && true || false;

        if (hasPoint) {
            addPoint(coordinatesToMap(coordinates));
            map.setZoom(coordinates.zoom);
            ctrl.toggleClass('mapboxgl-ctrl-add-point', false);
            ctrl.toggleClass('mapboxgl-ctrl-remove-point', true);
        }
    };

    var togglePoint = function() {
        var coordinates = getCoordinates(input);
        var hasPoint = (coordinates.lat && coordinates.lon) && true || false;

        if (hasPoint) {
            removePoint();
            setCoordinates(input, {'lat': null, 'lon': null, 'zoom': null});
        } else {
            var position = map.getCenter();
            addPoint(position);
            setCoordinates(input, mapToCoordinates(position, map.getZoom()));
        }
    };

    var addPoint = function(position) {
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [position.lng, position.lat]
                }
            }]
        };

        map.addSource('point', {
            "type": "geojson",
            "data": geojson
        });

        map.addLayer({
            "id": "point",
            "type": "circle",
            "source": "point",
            "paint": {
                "circle-radius": 10,
                "circle-color": "#000"
            }
        });
    };

    var removePoint = function() {
        map.removeSource('point');
        map.removeLayer('point');
    };

    function onMove(e) {
        if (!isDragging) {
            return;
        }

        var coords = e.lngLat;

        // Set a UI indicator for dragging.
        canvas.style.cursor = 'grabbing';

        // Update the Point feature in `geojson` coordinates
        // and call setData to the source layer `point` on it.
        geojson.features[0].geometry.coordinates = [coords.lng, coords.lat];
        map.getSource('point').setData(geojson);
        setCoordinates(input, mapToCoordinates(coords, map.getZoom()));
    }

    function onUp() {
        if (!isDragging) {
            return;
        }

        canvas.style.cursor = '';
        isDragging = false;
    }

    function mouseDown() {
        if (!isCursorOverPoint) {
            return;
        }

        isDragging = true;

        // Set a cursor indicator
        canvas.style.cursor = 'grab';

        // Mouse events
        map.on('mousemove', onMove);
        map.on('mouseup', onUp);
    }

    map.on('load', function() {
        initPoint();
    });

    ctrl.on('click', function(e) {
        ctrl.toggleClass('mapboxgl-ctrl-add-point');
        ctrl.toggleClass('mapboxgl-ctrl-remove-point');
        togglePoint();
        e.preventDefault();
    });

    // If a feature is found on map movement,
    // set a flag to permit a mousedown events.
    map.on('mousemove', function(e) {
        var features = map.queryRenderedFeatures(e.point, {layers: ['point']});

        // Change point and cursor style as a UI indicator
        // and set a flag to enable other mouse events.
        if (features.length) {
            map.setPaintProperty('point', 'circle-color', '#777');
            canvas.style.cursor = 'move';
            isCursorOverPoint = true;
            map.dragPan.disable();
        } else {
            map.setPaintProperty('point', 'circle-color', '#000');
            canvas.style.cursor = '';
            isCursorOverPoint = false;
            map.dragPan.enable();
        }
    });

    // Set `true` to dispatch the event before other functions call it. This
    // is necessary for disabling the default map dragging behaviour.
    map.on('mousedown', mouseDown, true);
}

var MapboxInput = function(input) {
    mapboxgl.accessToken = $('body').data('mapbox-token') || false;

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

    var language = ($('html').attr('lang') || 'de').split('-')[0];

    // the height depends on the width using the golden ratio
    el.css('height', input.data('map-height') || $(el).width() / 1.618 + 'px');

    var map = new mapboxgl.Map({
        container: el[0],
        style: 'mapbox://styles/mapbox/streets-v8',
        center: [lon, lat],
        zoom: zoom
    });

    map.addControl(new mapboxgl.Navigation());

    map.on('load', function() {
        var container = $(map._container);

        // language can only be set after loading
        map.setLayoutProperty('country-label-lg', 'text-field', '{name_' + language + '}');

        // buttons inside the map lead to form-submit if not prevented form it
        container.find('button').on('click', function(e) {
            e.preventDefault();
        });
    });

    switch (input.data('map-type')) {
        case 'crosshair':
            asCrosshairMap(map, input);
            break;
        case 'point':
            asPointMap(map, input);
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
