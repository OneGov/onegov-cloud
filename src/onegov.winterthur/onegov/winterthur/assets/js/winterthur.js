// custom map for winterthur
function spawnDefaultMap(target, options) {
    var service = 'https://stadtplan.winterthur.ch/wms/Hintergrundkarte_LK_AV_Situationsplan?';
    var layers = 'Hintergrundkarte_LK_AV_Situationsplan';
    var projection = L.CRS.EPSG4326

    var map = L.map(target, $.extend(options, {'crs': projection}));
    var tiles = L.tileLayer.wms(service, {layers: layers}).addTo(map);

    return map
}

// replace checkmarks in directory entries
$(document).ready(function() {
    $('.field-display dd').html(function() {
        return $(this).html().split('<br>').map(function(html) {
            return html.replace(/^\s*[✓\-]{1}/, ' •');
        }).join('<br>');
    });
});

// add hover clicks to directory entries
$(document).ready(function() {
    $('.with-thumbnails li').click(function(e) {
        window.location = $(this).find('a').attr('href');
        e.preventDefault();
    });
});

// the search reset button in the directory search resets the whole view
$(document).ready(function() {
    $('#inline-search .reset-button').click(function(e) {
        var $form = $(this).closest('form');
        var $inputs = $form.find('input');

        $inputs.val('');
        $form.find('input[name="search"]').val('inline');
        $inputs.filter(':visible:first').removeAttr('required');

        $form.submit();

        e.preventDefault();
    });
});
