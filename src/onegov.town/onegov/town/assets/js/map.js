// set the leaftlet images path
L.Icon.Default.imagePath = $('body').data('leaflet-images-folder');

// setup all maps
var setup_map = function(el) {

    el = $(el);

    var resize_map = function() {
        if (el.data('size') === 'fullscreen') {
            el.width($(window).width());
            el.height($(window).height());
        }
    };

    resize_map();
    $(window).on('resize', resize_map);

    var map = L.map(el[0]).setView([el.data('lat'), el.data('lon')], el.data('zoom'));

    var google = new L.Google('ROADMAP');
    map.addLayer(google);
};

$('.map').each(function() {
    setup_map(this);
});
