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

function spawnDefaultMap(target, options) {
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

    return map;
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
    $('.directory-entry-collection-layout .with-lead li').click(function(e) {
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

// adjust all links that point to an external domain to target _top in order
// to escape the iframe we're in
$(document).ready(function() {
    var internal = new RegExp("^http[s]?://(forms.winterthur.ch|" + window.location.hostname + ").*", "i");

    $('a[href^="http"]').each(function() {
        var a = $(this);

        if (!a.attr('href').match(internal)) {
            a.attr('target', '_top');
        }
    });
});
