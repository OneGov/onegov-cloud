/*
    Leaflet Vector Marker Template
*/
var vectorMarkerSVGTemplate = '<svg width="28" height="37" viewBox="0 0 28 37" xmlns="http://www.w3.org/2000/svg" version="1.1"><path transform="translate(2 2)" text-anchor="middle" fill="{{marker-color}}" fill-rule="nonzero" stroke="{{border-color}}" stroke-width="3" d="M12,0 C5.37136723,0 0,5.37130729 0,11.9998721 C0,14.6408328 0.85563905,17.0808246 2.30116496,19.0628596 L12,31.5826752 L21.698835,19.0628596 C23.1443609,17.0808246 24,14.6408328 24,11.9998721 C24,5.37130729 18.6286328,0 12,0 L12,0 Z"></path><text x="50%" y="50%" fill="{{icon-color}}" font-family="{{font_family}}" font-weight="{{font_weight}}" font-size="14" text-anchor="middle" alignment-baseline="center">{{icon}}</text></svg>';

var entry_counter = 0;
var entry_numbers = Array.from(document.getElementsByClassName("entry-number"));
// console.log(entry_numbers);
entry_numbers = entry_numbers.map(function(entry) {
    return entry.textContent.replace('. ', '');
});
// console.log(entry_numbers);

function VectorMarkerSVG(markerColor, borderColor, iconColor, icon) {
    font_family = 'inherit';
    if (icon === 'numbers') {
        icon = entry_counter + 1;
    } else if (icon === 'custom') {
        icon = entry_numbers[entry_counter];
    } else {
        icon = '&#x' + (icon || 'f111').replace('\\', '');
        font_family = fa_version === 5 && "'Font Awesome 5 Free'" || 'FontAwesome';
    }
    entry_counter += 1;
    return vectorMarkerSVGTemplate
        .replace('{{marker-color}}', markerColor)
        .replace('{{border-color}}', borderColor)
        .replace('{{icon-color}}', iconColor)
        .replace('{{icon}}', icon)
        .replace('{{font_family}}', font_family)
        .replace('{{font_weight}}', fa_version === 5 && '900' || 'regular');
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

function expandShorthandColor(color) {
    return color.replace(/^#?([a-f\d])([a-f\d])([a-f\d])$/i, function(_m, r, g, b) {
        return r + r + g + g + b + b;
    });
}

// RGB to Luma per ITU BT.601
function luma(color) {
    var rgb = parseInt(expandShorthandColor(color).replace('#', ''), 16);

    var r = (rgb >> 16) & 0xff;
    var g = (rgb >> 8) & 0xff;
    var b = (rgb >> 0) & 0xff;

    // RGB to Luma per ITU BT.601
    return 0.299 * r + 0.587 * g + 0.114 * b;
}

function isBrightColor(color) {
    return luma(color) >= 144;
}

function getMarkerOptions(input, overrides) {
    var body = $('body');
    var icon = input.data('marker-icon') || body.data('default-marker-icon') || 'f111';
    var markerColor = input.data('marker-color') || body.data('default-marker-color') || '#006fba';
    var iconColor = isBrightColor(markerColor) && '#000' || '#fff';

    return $.extend({
        markerColor: markerColor,
        iconColor: iconColor,
        icon: icon
    }, overrides || {});
}

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
    var icon = L.VectorMarkers.icon(getMarkerOptions(input));
    var draggableMarker = true;
    if (input.data('undraggable') !== undefined) {
        draggableMarker = false;
    }

    function fillAddressFormFields(geocode_result) {
        // Will fill in your form fields with the fetched geocoded address result.
        // Can be used in combination with the CoordinatesField that uses a marker map to store the address at the same
        // time as the coordinates
        var addrInput = $('input#address');
        var zipCodeInput = $('input#zip_code');
        var cityInput = $('input#city');
        var countryInput = $('input#country');

        if (addrInput.length && zipCodeInput.length && cityInput.length) {
            var properties = geocode_result.properties;
            addrInput.val([properties.text || '', properties.address || ''].join(' ').trim());
            zipCodeInput.val(properties.postcode || '');
            cityInput.val(properties.place || '');
            if (countryInput.length) {
                countryInput.val(properties.country || '');
            }
        }
    }

    function addMarker(position, zoom, title) {
        position = position || map.getCenter();
        zoom = zoom || map.getZoom();
        title = title || '';
        marker = L.marker(position, {icon: icon, draggable: draggableMarker, title});
        marker.addTo(map);
        if (map.getZoom() !== zoom) {
            // setZoom will reset the animation and potentially screw
            // our position, so we stop the animation and do a flyTo
            // instead which sets both parameters at once, but we only
            // need to do this if the zoom level has been changed
            map.stop();
            map.flyTo(position, zoom);
        }

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

    var hasMarker = function() {
        return pointButton._currentState.stateName === 'remove-point';
    };

    pointButton.addTo(map);

    if (coordinates.lat && coordinates.lon) {
        addMarker(coordinatesToMap(coordinates), coordinates.zoom);
        pointButton.state('remove-point');
    }

    map.on('geocode-marked', function(result) {
        if (hasMarker()) {
            removeMarker();
        }
        var position = new L.LatLng(result.geocode.center.lat, result.geocode.center.lng);
        addMarker(position, null, result.geocode.name);
        fillAddressFormFields(result.geocode);
        pointButton.state('remove-point');
    });

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
            icon: fa_version === 5 && 'fas fa-external-link-alt' || 'fa-external-link',
            onClick: function(btn) {
                var menu = $('<ul class="map-context-menu">');
                var point = map.getCenter();

                $('<li><a href="http://maps.google.com/?q=' + [point.lat, point.lng].join(',') + '" target="_blank">Google Maps</a></li>').appendTo(menu);
                $('<li><a href="http://maps.apple.com/?q=' + [point.lat, point.lng].join(',') + '" target="_blank">Apple Maps</a></li>').appendTo(menu);
                if (map.options.custom_map === 'map-bs') {
                    var point_ch = map.options.crs.project(point);
                    $('<li><a  id="map-bs-button" href="https://map.geo.bs.ch/?lang=de&baselayer_ref=Grundkarte%20farbig&map_crosshair=true&map_x=' + point_ch.x + '&map_y=' + point_ch.y + '&map_zoom=8" target="_blank">Karte Geo-BS</a></li>').appendTo(menu);
                }

                menu.insertAfter($(btn.button));
                btn.state('open');
            }
        }, {
            stateName: 'open',
            icon: fa_version === 5 && 'fas fa-external-link-alt' || 'fa-external-link',
            onClick: function(btn) {
                $(btn.button).parent().find('.map-context-menu').remove();
                btn.state('closed');
            }
        }]
    }).addTo(map);
}

function getMapboxToken() {
    return $('body').data('mapbox-token') || false;
}

function getLanguage() {
    return ($('html').attr('lang') || 'de').substring(0, 2);
}

function addGeocoder(map) {
    var lang = getLanguage();

    // there's no translation layer for onegov.gis yet and this lone string
    // is not enough to justify adding one
    var placeholder = {
        'de': _("Nach Adresse suchen"),
        'fr': _("Rechercher une adresse"),
        'en': _("Lookup address")
    };

    L.Control.geocoder({
        position: 'topleft',
        placeholder: placeholder[lang] || placeholder.de,
        errorMessage: '',
        defaultMarkGeocode: false,
        collapsed: false,
        showResultIcons: true,
        geocoder: (new L.Control.Geocoder.Mapbox(getMapboxToken(), {
            geocodingQueryParams: {
                'language': getLanguage(),
                // this is the geographical center of Switzerland, which gets
                // mapbox to prefer Switzerland results, without a limit
                'proximity': [8.2318, 46.7985],
                'limit': 3
            }
        }))
    }).on('markgeocode', function(e) {
        map.panTo(new L.LatLng(e.geocode.center.lat, e.geocode.center.lng));
        map.fire('geocode-marked', e);
        this._clearResults();
    }).addTo(map);
}

function addLocate(map) {
    var lang = getLanguage();

    // there's no translation layer for onegov.gis yet
    var strings = {
        'de': {
            title: _("Mein Standort"),
            errorTitle: _("Fehler"),
            outsideMapBoundsMsg: _("Sie scheinen sich ausserhalb der Grenzen der Karte zu befinden")
        },
        'fr': {
            title: _("Ma position"),
            errorTitle: _("Erreur"),
            outsideMapBoundsMsg: _("Vous semblez vous trouver en dehors des limites de la carte")
        },
        'en': {
            title: _("My Location"),
            errorTitle: _("Error"),
            outsideMapBoundsMsg: _("You seem located outside the boundaries of the map")
        }
    };
    strings = strings[lang] || strings.de;

    var error_strings = {
        'de': [
            _("Geolokalisierung wird auf Ihrem Gerät nicht unterstützt"),
            _("Die Erlaubnis zur Geolokalisierung wurde verweigert"),
            _("Ihre Position konnte auf Ihrem Gerät nicht ermittelt werden"),
            _("Die Geolokalisierung dauerte zu lange")
        ],
        'fr': [
            _("La géolocalisation n'est pas prise en charge par votre appareil"),
            _("L'autorisation de géolocalisation a été refusée"),
            _("L'obtention des informations de géolocalisation a pris trop de temps"),
            _("Geolocation took too long to respond")
        ],
        'en': [
            _("Geolocation is not supported on your device"),
            _("Geolocation permission was denied"),
            _("Geolocation could not be determined on your device"),
            _("Geolocation information took too long to obtain")
        ]
    };
    error_strings = error_strings[lang] || error_strings.de;

    var locate = L.control.locate({
        position: 'topleft',
        setView: 'once',
        locateOptions: {
            enableHighAccuracy: true
        },
        clickBehavior: {
            outOfView: 'stop'
        },
        showCompass: false,
        drawCircle: false,
        drawMarker: false,
        showPopup: false,
        icon: 'fa fa-location-arrow',
        iconLoading: 'fa fa-spinner',
        strings: strings
    }).addTo(map);

    map.on('locationfound', function(e) {
        locate.stop();
        var geocode = {
            name: strings.title,
            bbox: e.bbox,
            center: e.latlng,
            properties: {}
        };
        map.panTo(e.latlng);
        map.fire('geocode-marked', {geocode: geocode});
    }).on('locationerror', function(e) {
        locate.stop();
        map.openPopup(
            '<span class="popup-title">' + strings.errorTitle + '</span>' +
            '<div class="popup-lead">' +
            (error_strings[e.code] || e.message) +
            '</div>',
            map.getCenter()
        );
    });
}

function getMapboxTiles() {
    var url = 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}';

    return L.tileLayer(url, {
        attribution: '<ul><li><a href="https://www.mapbox.com/map-feedback/">© Mapbox</a></li><li><a href="http://www.openstreetmap.org/copyright">© OpenStreetMap</a></li></ul>',
        tileSize: 512,
        zoomOffset: -1,
        id: 'mapbox/streets-v11',
        accessToken: getMapboxToken()
    });
}

function spawnMapboxMap(target, options) {
    return L.map(target, options).addLayer(getMapboxTiles());
}

function spawnDefaultMap(target, options, cb) {
    cb(spawnMapboxMap(target, options));
}

function spawnMap(element, lat, lon, zoom, includeZoomControls, cb) {
    let $el = $(element);

    let lang = getLanguage();

    // there's no translation layer for onegov.gis yet
    let strings = {
        'de': {
            clickToActivate: _("Klicken Sie zur Aktivierung der Karte")
        },
        'fr': {
            clickToActivate: _("Cliquez pour activer la carte")
        },
        'en': {
            clickToActivate: _("Click to activate map")
        }
    };
    strings = strings[lang] || strings.de;

    // the height is calculated form the width using the golden ratio
    element.css('height', $el.data('map-height') || $el.width() / 1.618 + 'px');

    let options = {
        zoomControl: false,
        sleepNote: false,
        sleepTime: 500,
        wakeTime: 500,
        sleepOpacity: 1.0,
        preferCanvas: true
    };

    spawnDefaultMap(element[0], options, function(map) {
        map.setView([lat, lon], zoom);

        function addBlocker() {
            const isOnEditPage = window.location.href.endsWith('+edit');
            if (!isOnEditPage) {
                return;
            }

            // Add a blocker to prevent interaction with the map until clicked
            const blocker = L.DomUtil.create('div', 'map-event-blocker');
            blocker.style.position = 'absolute';
            blocker.style.top = '0';
            blocker.style.left = '0';
            blocker.style.right = '0';
            blocker.style.bottom = '0';
            blocker.style.zIndex = '1000';
            blocker.style.backgroundColor = 'rgba(0, 0, 0, 0.1)';
            blocker.style.cursor = 'pointer';
            blocker.style.display = 'flex';
            blocker.style.alignItems = 'center';
            blocker.style.justifyContent = 'center';

            const message = L.DomUtil.create('div', 'map-click-message');
            message.innerHTML = strings.clickToActivate;
            message.style.backgroundColor = 'white';
            message.style.padding = '8px 16px';
            message.style.borderRadius = '4px';
            message.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            message.style.fontSize = '14px';

            blocker.appendChild(message);
            map.getContainer().appendChild(blocker);

            // Block all events
            L.DomEvent
                .on(blocker, 'mousewheel', L.DomEvent.stopPropagation)
                .on(blocker, 'wheel', L.DomEvent.stopPropagation)
                .on(blocker, 'mousedown', L.DomEvent.stopPropagation)
                .on(blocker, 'touchstart', L.DomEvent.stopPropagation)
                .on(blocker, 'dblclick', L.DomEvent.stopPropagation)
                .on(blocker, 'contextmenu', L.DomEvent.stopPropagation)
                .on(blocker, 'click', function(e) {
                    blocker.remove();
                    L.DomEvent.stopPropagation(e);
                });

            return blocker;
        }

        // Add initial blocker
        addBlocker();

        // Add click handler to document to re-add blocker when clicking outside
        $(document).on('click', function(e) {
            if (!$(e.target).closest(map.getContainer()).length) {
                if (!map.getContainer().querySelector('.map-event-blocker')) {
                    addBlocker();
                }
            }
        });

        // remove leaflet link - we don't advertise other open source projects
        // we depend on as visibly either
        map.attributionControl.setPrefix('');

        if (typeof includeZoomControls === 'undefined' || includeZoomControls) {
            new L.Control.Zoom({position: 'topright'}).addTo(map);
        }

        map.on('load', function() {
            var container = $(map._container);
            // buttons inside the map lead to form-submit if not prevented form it
            container.find('button').on('click', function(e) {
                e.preventDefault();
            });
        });

        document.leafletmaps = document.leafletmaps || [];
        document.leafletmaps.push(map);
        cb(map);
    });
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

    spawnMap(el, lat, lon, zoom, true, function(map) {
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
        addLocate(map);
    });
};

var MapboxMarkerMap = function(target) {
    var lat = target.data('lat');
    var lon = target.data('lon');
    var zoom = target.data('zoom') || $('body').data('default-zoom') || 10;
    var includeZoomControls = target.data('map-type') !== 'thumbnail';

    spawnMap(target, lat, lon, zoom, includeZoomControls, function(map) {
        addExternalLinkButton(map);

        /* for now we do not support clicking the marker, so we use marker-noclick
        as a way to disable the pointer cursor */
        var icon = L.VectorMarkers.icon(getMarkerOptions(target, {
            extraClasses: ['marker-' + target.data('map-type')]
        }));

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
    });
};

var MapboxGeojsonMap = function(target) {
    // a map that displays a large number of map markers
    var lat = target.data('lat');
    var lon = target.data('lon');
    var zoom = target.data('zoom');
    var includeZoomControls = true;

    spawnMap(target, lat, lon, zoom, includeZoomControls, function(map) {
        var icon = L.VectorMarkers.icon(getMarkerOptions(target));

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
                    '<div class="popup-lead">' + (feature.properties.lead || '') + '</div>'
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
