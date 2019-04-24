var parseXML = function(text) {
    return (new window.DOMParser()).parseFromString(text, 'text/xml');
};

var fetchXML = function(url, cb) {
    var r = new XMLHttpRequest();
    r.onreadystatechange = function() {
        if (this.readyState !== 4 || this.status !== 200) {
            return;
        }

        cb(parseXML(r.responseText));
    };
    r.open("GET", url, true);
    r.send();
};

var firstMatch = function(list, match) {
    for (var i = 0; i < list.length; i++) {
        if (match(list[i])) {
            return list[i];
        }
    }

    return null;
};

var asInt = function(text) {
    return parseInt(text, 10);
};

var splitTag = function(tag) {
    var parts = tag.split(':', 2);

    if (parts.length === 1) {
        return ['*', tag];
    }

    return parts;
};

var getElement = function(root, tag) {
    var parts = splitTag(tag);
    var ns = parts[0];
    var name = parts[1];

    var elements = [];

    // about every browser and browser version handles this differently, so
    // we need to check a number of ways and fall back step by step
    elements = root.getElementsByTagName(tag);
    if (elements.length > 0) {
        return elements;
    }

    elements = root.getElementsByTagNameNS(ns, name);
    if (elements.length > 0) {
        return elements;
    }

    elements = root.getElementsByTagNameNS('*', name);
    if (elements.length > 0) {
        return elements;
    }

    elements = root.getElementsByTagName(name);
    if (elements.length > 0) {
        return elements;
    }

    return elements;
};

var Lookup = function(element) {
    var self = this;

    self.element = element;

    self.one = function(tag) {
        return getElement(self.element, tag)[0];
    };

    self.all = function(tag) {
        return getElement(self.element, tag);
    };

    self.get = function(tag) {
        return self.one(tag).textContent;
    };

    return self;
};

// Loads geo capabilities and stores the relevant information as an object
var Capabilities = function(url) {
    var self = this;
    self.loaded = false;

    var get = function(xml, tag) {
        return getElement(xml, tag)[0].textContent;
    };

    var extractMatrix = function(xml) {
        var tms = new Lookup(
            firstMatch(getElement(xml, 'TileMatrixSet'), function(element) {
                return (element.children && element.children.length !== 0) ||
                // childNodes include text nodes (usually 1)
                (element.childNodes && element.childNodes.length > 1);
            })
        );

        var matrix = {
            boundingBox: [
                tms.get('ows:LowerCorner').split(' ').map(asInt),
                tms.get('ows:UpperCorner').split(' ').map(asInt)
            ],
            tiles: []
        };

        var tiles = tms.all('TileMatrix');
        for (var i = 0; i < tiles.length; i++) {
            var t = tiles[i];

            matrix.tiles.push({
                identifier: get(t, 'ows:Identifier'),
                scaleDenominator: parseFloat(get(t, 'ScaleDenominator')),
                topLeftCorner: get(t, 'TopLeftCorner').split(' ').map(asInt),
                tileWidth: asInt(get(t, 'TileWidth')),
                tileHeight: asInt(get(t, 'TileHeight')),
                matrixWidth: asInt(get(t, 'MatrixWidth')),
                matrixHeight: asInt(get(t, 'MatrixHeight'))
            });
        }

        return matrix;
    };

    var getCRS = function(matrix) {
        var pixelWidth = 0.00028;

        var crs = new L.Proj.CRS(
            'EPSG:2056',
            [
                '+proj=somerc',
                '+lat_0=46.95240555555556',
                '+lon_0=7.439583333333333',
                '+k_0=1',
                '+x_0=2600000',
                '+y_0=1200000',
                '+ellps=bessel',
                '+towgs84=674.374,15.056,405.346,0,0,0,0',
                '+units=m',
                '+no_defs'
            ].join(' '),
            {
                resolutions: matrix.tiles.map(function(t) {
                    return t.scaleDenominator * pixelWidth;
                })
            }
        );

        return crs;
    };

    fetchXML(url, function(xml) {
        self.matrix = extractMatrix(xml);
        self.crs = getCRS(self.matrix);

        self.loaded = true;
    });

    self.ready = function(cb) {
        var poll = 10;

        setTimeout(function() {
            if (self.loaded === true) {
                cb.call(self);
            } else {
                self.ready(cb);
            }
        }, poll);
    };

    return self;
};

function spawnZugMap(target, options, cb, url, definition, layer) {
    (new Capabilities(definition)).ready(function() {
        var matrix = this.matrix;
        var crs = this.crs;

        var service = url + "/service.svc/get" +
            "?layer=" + layer +
            "&style=Default" +
            "&tilematrixset=" + layer +
            "&Service=WMTS" +
            "&Request=GetTile" +
            "&Version=1.0.0" +
            "&Format=image/png" +
            "&TileMatrix={z}" +
            "&TileCol={x}" +
            "&TileRow={y}";

        // we got the capabilities so now we can create our own tile layer
        var ZugMapLayer = L.TileLayer.extend({
            getTileUrl: function(coordinates) {
                var zoom = this._getZoomForUrl();
                var level = matrix.tiles[zoom];
                var bounds = this._tileCoordsToNwSe(coordinates);
                var nw = crs.project(bounds[0]);
                var se = crs.project(bounds[1]);

                var width = se.x - nw.x;
                var height = nw.y - se.y;

                var tilecol = +Number(Math.floor((nw.x - level.topLeftCorner[0]) / width));
                var tilerow = -Number(Math.floor((nw.y - level.topLeftCorner[1]) / height));

                return L.Util.template(service, {
                    x: tilecol,
                    y: tilerow,
                    z: zoom
                });
            }
        });

        var map = L.map(target, $.extend(options, {
            crs: crs
        }));

        (new ZugMapLayer(service, {
            minZoom: 0,
            maxZoom: matrix.tiles.length - 1,
            tileSize: 512
        })).addTo(map);

        cb(map);
    });
}
