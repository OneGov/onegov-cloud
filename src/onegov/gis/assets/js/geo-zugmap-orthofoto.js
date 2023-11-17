function spawnDefaultMap(target, options, cb) {
    var matrix = this.matrix;
    // configuration for lv95 coordinates. Please do not change.
    let lv95 = {
        epsg: 'EPSG:2056',
        def: '+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=2600000 +y_0=1200000 +ellps=bessel +towgs84=674.374,15.056,405.346,0,0,0,0 +units=m +no_defs ',
        resolutions: [26.45833332, 19.84374999, 13.22916666, 10.583333328, 7.937499996, 6.61458333, 5.291666664, 3.968749998, 3.307291665, 2.6458333322,
            1.9843749999, 1.3229166666, 0.7937499996, 0.6614583333, 0.5291666667, 0.3968749998, 0.2645833333, 0.1984374999, 0.1322916667, 0.0793749999,
            0.0661458333, 0.0529166666, 0.0396874999, 0.0264583333, 0.0132291667],
        origin: [2670000, 1235000],
    }

    var crs = new L.Proj.CRS(lv95.epsg, lv95.def, {
        resolutions: lv95.resolutions,
        origin: lv95.origin
    })

    var map = L.map(target, $.extend(options, {
        crs: crs,
        maxZoom: lv95.resolutions.length,
        custom_map: 'map-zg'
    }));

    L.tileLayer('https://services.geo.zg.ch/tc/wmts/1.0.0/zg.orthofoto/default/zg/{z}/{y}/{x}.png', {
        tileSize: 512,
        maxZoom: lv95.resolutions.length,
        id: 'zg.orthofoto',
        }).addTo(map);

    cb(map);
}
