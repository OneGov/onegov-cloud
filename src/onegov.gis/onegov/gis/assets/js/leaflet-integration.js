/*
    Leaflet Vector Marker Template
*/
var vectorMarkerSVGTemplate = '<svg width="28" height="37" viewBox="0 0 28 37" xmlns="http://www.w3.org/2000/svg" version="1.1"><path transform="translate(2 2)" text-anchor="middle" fill="{{marker-color}}" fill-rule="nonzero" stroke="{{border-color}}" stroke-width="3" d="M12,0 C5.37136723,0 0,5.37130729 0,11.9998721 C0,14.6408328 0.85563905,17.0808246 2.30116496,19.0628596 L12,31.5826752 L21.698835,19.0628596 C23.1443609,17.0808246 24,14.6408328 24,11.9998721 C24,5.37130729 18.6286328,0 12,0 L12,0 Z"></path><text x="50%" y="50%" fill="{{icon-color}}" font-family="FontAwesome" font-size="14" text-anchor="middle" alignment-baseline="center">{{icon}}</text></svg>';

function VectorMarkerSVG(markerColor, borderColor, iconColor, icon) {
    icon = '&#x' + (icon || 'f111').replace('\\', '');
    return vectorMarkerSVGTemplate
        .replace('{{marker-color}}', markerColor)
        .replace('{{border-color}}', borderColor)
        .replace('{{icon-color}}', iconColor)
        .replace('{{icon}}', icon);
}

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
        extraClasses: [],
        icon: "f111",
        markerColor: "blue",
        borderColor: "white",
        iconColor: "white",
        popupAnchor: [1, -31],
        size: [28, 37]
    },
    initialize: function(options) {
        return L.Util.setOptions(this, options);
    },
    createIcon: function(oldIcon) {
        var div = (oldIcon && oldIcon.tagName === "DIV" ? oldIcon : document.createElement("div"));

        div.innerHTML = VectorMarkerSVG(
            this.options.markerColor,
            this.options.borderColor,
            this.options.iconColor,
            this.options.icon
        );

        div.classList.add(this.options.className);
        for (var i = 0; i < this.options.extraClasses.length; i++) {
            div.classList.add(this.options.extraClasses[i]);
        }

        var size = L.point(this.options.size);
        div.style.marginLeft = (-size.x / 2) + 'px';
        div.style.marginTop = (-size.y) + 'px';

        return div;
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

function asThumbnailMap(map) {
    // a map that acts as a thumbnail, offering no interaction, instead
    // linking to better maps (like google maps, osm and so on)
    map.dragging.disable();
    map.touchZoom.disable();
    map.doubleClickZoom.disable();
    map.scrollWheelZoom.disable();
    map.boxZoom.disable();
    map.keyboard.disable();
    map._container.style.cursor = 'default';

    if (map.tap) {
        map.tap.disable();
    }
}

function addExternalLinkButton(map) {
    L.easyButton({
        position: 'topright',
        states: [{
            stateName: 'closed',
            icon: 'fa-external-link',
            onClick: function(btn) {
                var menu = $('<ul class="map-context-menu">');
                var point = map.getCenter();

                $('<li><a href="http://maps.google.com/?q=' + [point.lat, point.lng].join(',') + '" target="_blank">Google Maps</a></li>').appendTo(menu);
                $('<li><a href="http://maps.apple.com/?q=' + [point.lat, point.lng].join(',') + '" target="_blank">Apple Maps</a></li>').appendTo(menu);

                menu.insertAfter($(btn.button));
                btn.state('open');
            }
        }, {
            stateName: 'open',
            icon: 'fa-external-link',
            onClick: function(btn) {
                $(btn.button).parent().find('.map-context-menu').remove();
                btn.state('closed');
            }
        }]
    }).addTo(map);
}

function addGeocoder(map) {
    L.Control.geocoder({
        position: 'topleft',
        placeholder: '',
        errorMessage: '',
        defaultMarkGeocode: false
    }).on('markgeocode', function(e) {
        map.panTo(new L.LatLng(e.geocode.center.lat, e.geocode.center.lng));
    }).addTo(map);
}

function getMapboxToken() {
    return $('body').data('mapbox-token') || false;
}

function getTiles() {
    var url = 'https://api.mapbox.com/v4/mapbox.streets/{z}/{x}/{y}';
    url += (L.Browser.retina ? '@2x.png' : '.png');
    url += '?access_token=' + getMapboxToken();

    return L.tileLayer(url, {
        attribution: '<ul><li><a href="https://www.mapbox.com/map-feedback/">© Mapbox</a></li><li><a href="http://www.openstreetmap.org/copyright">© OpenStreetMap</a></li></ul>'
    });
}

function spawnDefaultMap(element, lat, lon, zoom, includeZoomControls) {

    // the height is calculated form the width using the golden ratio
    element.css('height', $(element).data('map-height') || $(element).width() / 1.618 + 'px');

    var options = {
        zoomControl: false,
        sleepNote: false,
        sleepTime: 500,
        wakeTime: 500,
        sleepOpacity: 1.0,
        preferCanvas: true
    };

    var map = L.map(element[0], options)
        .addLayer(getTiles())
        .setView([lat, lon], zoom);

    if (typeof includeZoomControls === 'undefined' || includeZoomControls) {
        new L.Control.Zoom({position: 'topright'}).addTo(map);
    }

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

    document.leafletmaps = document.leafletmaps || [];
    document.leafletmaps.push(map);

    return map;
}

var MapboxInput = function(input) {
    var coordinates = getCoordinates(input);

    // the default is seantis hq - as good a place as any
    var body = $('body');
    var lat = parseFloat(coordinates.lat || body.data('default-lat') || 47.0517251);
    var lon = parseFloat(coordinates.lon || body.data('default-lon') || 8.3054817);
    var zoom = parseInt(coordinates.zoom || body.data('default-zoom') || 5, 10);

    input.hide();

    // the map introduces buttons which would override the default button used
    // when pressing enter on a form, therefore we're adding a hack to prevent
    // this from happening
    var form = $(input.closest('form'));
    form.find('input').keypress(function(e) {
        if (e.which === 13) {
            e.preventDefault();
            form.find('input[type="submit"]:last').click();
        }
    });

    var label = input.closest('label');

    var wrapper = $('<div class="map-wrapper">').insertAfter(label);

    if (input.attr('placeholder')) {
        $('<div class="placeholder">' + input.attr('placeholder') + '</div>').appendTo(label);
    }

    var el = $('<div class="map">')
        .appendTo(wrapper);

    var map = spawnDefaultMap(el, lat, lon, zoom);

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

    addGeocoder(map);
};

var MapboxMarkerMap = function(target) {
    var lat = target.data('lat');
    var lon = target.data('lon');
    var zoom = target.data('zoom') || $('body').data('default-zoom') || 10;
    var includeZoomControls = target.data('map-type') !== 'thumbnail';

    var map = spawnDefaultMap(target, lat, lon, zoom, includeZoomControls);
    addExternalLinkButton(map);

    /* for now we do not support clicking the marker, so we use marker-noclick
    as a way to disable the pointer cursor */
    var icon = L.VectorMarkers.icon({
        extraClasses: ['marker-' + target.data('map-type')],
        markerColor: target.data('marker-color') || $('body').data('default-marker-color') || '#006fba'
    });

    var marker = L.marker({'lat': lat, 'lng': lon}, {
        icon: icon,
        draggable: false
    });
    marker.addTo(map);

    switch (target.data('map-type')) {
        case 'thumbnail':
            asThumbnailMap(map, target);
            break;
        default:
            break;
    }
};

var MapboxGeojsonMap = function(target) {
    // a map that displays a large number of map markers

    var lat = target.data('lat');
    var lon = target.data('lon');
    var zoom = target.data('zoom');
    var includeZoomControls = true;
    var map = spawnDefaultMap(target, lat, lon, zoom, includeZoomControls);

    var icon = L.VectorMarkers.icon({
        markerColor: $('body').data('default-marker-color') || '#006fba'
    });

    var pointToLayer = function(_feature, latlng) {
        return L.marker({'lat': latlng.lat, 'lng': latlng.lng}, {
            icon: icon
        });
    };

    var onEachFeature = function(feature, layer) {
        if (feature.properties) {
            layer.bindPopup(
                '<a class="popup-title" href="' + feature.properties.link + '">' +
                feature.properties.title +
                '</a>' +
                '<div class="popup-lead">' + feature.properties.lead + '</div>'
            );
        }
    };

    $.getJSON(target.data('geojson'), function(features) {
        if (features.length === 0) {
            return;
        }

        var layer = L.geoJSON(features, {
            pointToLayer: pointToLayer,
            onEachFeature: onEachFeature
        }).addTo(map);

        map.fitBounds(layer.getBounds().pad(0.185), {maxZoom: zoom});
    });
};

jQuery.fn.mapboxInput = function() {
    return this.each(function() {
        MapboxInput($(this));
    });
};

jQuery.fn.mapboxMarkerMap = function() {
    return this.each(function() {
        MapboxMarkerMap($(this));
    });
};

jQuery.fn.mapboxGeojsonMap = function() {
    return this.each(function() {
        MapboxGeojsonMap($(this));
    });
};

$(document).ready(function() {
    $('input.coordinates').mapboxInput();
    $('.marker-map').mapboxMarkerMap();
    $('.geojson-map').mapboxGeojsonMap();
});
