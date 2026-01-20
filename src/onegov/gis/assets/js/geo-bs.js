function spawnDefaultMap(target, options, cb) {
        var matrix = this.matrix;
        var lv95 = {
            epsg: 'EPSG:2056',
            def: '+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=2600000 +y_0=1200000 +ellps=bessel +towgs84=674.374,15.056,405.346,0,0,0,0 +units=m +no_defs',
            resolutions: [50,20,10,5,2.5,2,1.5,1,0.5,0.25,0.1,0.05,0.025,0.01],
            origin: [2550000,1315000]
           }
        
        var crs = new L.Proj.CRS(lv95.epsg, lv95.def, { 
            resolutions: lv95.resolutions, 
            origin: lv95.origin
        })
        
        var map = L.map(target, $.extend(options, {
            crs: crs,
            maxZoom: crs.options.resolutions.length,
            custom_map: 'map-bs'
        }));
        
        L.tileLayer('https://wmts.geo.bs.ch/wmts/1.0.0/BaseMap_farbig/default/swissgrid/{z}/{y}/{x}.png', {
            maxZoom: crs.options.resolutions.length,
            }).addTo(map);
        
        cb(map);
}
