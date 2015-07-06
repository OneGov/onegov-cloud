// set the leaftlet images path
L.Icon.Default.imagePath = document.body.getAttribute('data-leaflet-images-folder');

// setup all maps
var setup_map = function(el) {

    var resize_map = function() {
        if (el.getAttribute('data-size') === 'fullscreen') {
            el.style.width = window.innerWidth.toString() + 'px';
            el.style.height = window.innerHeight.toString() + 'px';
        }
    };

    window.onresize = resize_map;
    resize_map();

    var lat = parseFloat(el.getAttribute('data-lat'));
    var lon = parseFloat(el.getAttribute('data-lon'));
    var zoom = parseInt(el.getAttribute('data-zoom'), 10);

    var map = L.map(el).setView([lat, lon], zoom);

    var google = new L.Google('ROADMAP');
    map.addLayer(google);
};

var maps = document.getElementsByClassName('map');

for (var i=0; i<maps.length; i++) {
    setup_map(maps[i]);
}
