// custom map for winterthur
function epsg_2056_projection() {
    return new L.Proj.CRS(
        'EPSG:2056',
        [
            '+title=CH1903 / LV95',
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
            // all zoomed out -> all zoomed in
            scales: [
                0.0625,
                0.125,
                0.25,
                0.5,
                1,
                3
            ]
        }
    );
}

function spawnDefaultMap(target, options, cb) {
    var service = 'https://stadtplan.winterthur.ch/wms/Hintergrundkarte_LK_AV_Situationsplan?';
    var layers = 'Hintergrundkarte_LK_AV_Situationsplan';
    var projection = epsg_2056_projection();
    var maxZoom = projection._scales.length - 1;

    var map = L.map(target, $.extend(options, {
        'crs': projection,
        'zoom': 0
    }));
    L.tileLayer.wms(service, {
        'layers': layers,
        'maxZoom': maxZoom,
        'minZoom': 0
    }).addTo(map);

    cb(map);
}
