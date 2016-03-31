/*
    Leaflet Vector Marker (ish)

    This is not actually leaflet-vector marker anymore, it's the same idea and
    some of the code, but it's much smaller and does way less.
*/
L.VectorMarkers = {};
L.VectorMarkers.version = "1.1.0";
L.VectorMarkers.Icon = L.Icon.extend({
    options: {
        className: "vector-marker",
        prefix: "fa",
        icon: "fa-circle",
        markerColor: "blue",
        strokeColor: "white",
        iconColor: "white",
        popupAnchor: [1, -27],
        size: [30, 39],
        svg: '<?xml version="1.0" encoding="UTF-8" standalone="no"?><svg width="30px" height="39px" viewBox="0 0 30 39" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><path d="M15,3 C8.37136723,3 3,8.37130729 3,14.9998721 C3,17.6408328 3.85563905,20.0808246 5.30116496,22.0628596 L15,34.5826752 L24.698835,22.0628596 C26.1443609,20.0808246 27,17.6408328 27,14.9998721 C27,8.37130729 21.6286328,3 15,3 L15,3 Z" id="marker" stroke="{{stroke-color}}" stroke-width="3" fill="{{color}}"></path></g></svg>'
    },
    initialize: function(options) {
        return L.Util.setOptions(this, options);
    },
    createIcon: function(oldIcon) {
        var div = (oldIcon && oldIcon.tagName === "DIV" ? oldIcon : document.createElement("div"));
        div.innerHTML = this.options.svg
            .replace('{{color}}', this.options.markerColor)
            .replace('{{stroke-color}}', this.options.strokeColor);
        div.classList.add(this.options.className);

        if (this.options.icon) {
            div.appendChild(this.createInnerIcon());
        }

        var size = L.point(this.options.size);

        div.style.marginLeft = (-size.x / 2) + 'px';
        div.style.marginTop = (-size.y) + 'px';

        return div;
    },
    createInnerIcon: function() {
        var i = document.createElement('i');

        i.classList.add(this.options.prefix);
        i.classList.add(this.options.icon);
        i.style.color = this.options.iconColor;

        return i;
    }
});

L.VectorMarkers.icon = function(options) {
    return new L.VectorMarkers.Icon(options);
};

/*
    Leaflet Map Input (setting of coordinates in forms)
*/

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

function asMarkerMap(map, input) {
    // a map that provides a single marker which can be added, moved or removed
    // from the map

    var marker;
    var coordinates = getCoordinates(input);
    var icon = L.VectorMarkers.icon({
        prefix: 'fa',
        icon: 'fa-circle',
        markerColor: input.data('marker-color') || $('body').data('default-marker-color') || '#006fba'
    });

    function addMarker(position, zoom) {
        position = position || map.getCenter();
        zoom = zoom || map.getZoom();

        marker = L.marker(position, {icon: icon, draggable: true});
        marker.addTo(map);
        map.setZoom(zoom);

        marker.on('dragend', function() {
            setCoordinates(
                input,
                mapToCoordinates(marker.getLatLng(), map.getZoom())
            );
        });

        setCoordinates(input, mapToCoordinates(position, map.getZoom()));
    }

    function removeMarker() {
        map.removeLayer(marker);
        setCoordinates(input, {'lat': null, 'lon': null, zoom: null});
    }

    var pointButton = L.easyButton({
        position: 'topright',
        states: [{
            stateName: 'add-point',
            icon:      'fa-map-marker',
            title:     'Add marker',
            onClick: function(btn) {
                addMarker();
                btn.state('remove-point');
            }
        }, {
            stateName: 'remove-point',
            icon:      'fa-trash',
            title:     'Remove marker',
            onClick: function(btn) {
                removeMarker();
                btn.state('add-point');
            }
        }]
    });

    pointButton.addTo(map);

    if (coordinates.lat && coordinates.lon) {
        addMarker(coordinatesToMap(coordinates), coordinates.zoom);
        pointButton.state('remove-point');
    }

    map.on('zoomend', function() {
        var c = getCoordinates(input);
        c.zoom = map.getZoom();

        setCoordinates(input, c);
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

    var options = {
        zoomControl: false
    };

    var map = L.map(el[0], options)
        .addLayer(getTiles())
        .setView([lat, lon], zoom);

    new L.Control.Zoom({position: 'topright'}).addTo(map);

    // remove leaflet link - we don't advertise other open source projects
    // we depend on as visibly either
    map.attributionControl.setPrefix('');

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
        case 'marker':
            asMarkerMap(map, input);
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
