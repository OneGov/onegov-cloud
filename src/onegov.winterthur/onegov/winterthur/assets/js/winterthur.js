function spawnDefaultMap(target, options) {
    var service = 'http://stadtplan.winterthur.ch/wms/Hintergrundkarte_LK_AV_Situationsplan?';
    var layers = 'Hintergrundkarte_LK_AV_Situationsplan';
    var projection = L.CRS.EPSG4326

    var map = L.map(target, $.extend(options, {'crs': projection}));
    var tiles = L.tileLayer.wms(service, {layers: layers}).addTo(map);

    return map
}

$(document).ready(function() {
    $('.field-display dd').html(function() {
        return $(this).html().split('<br>').map(function(html) {
            return html.replace(/\s*[✓\-]{1}/, ' •');
        }).join('<br>');
    });
});
