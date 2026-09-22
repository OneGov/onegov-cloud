var header_height = $('#header').height();

let header = document.getElementById('header');


header.addEventListener('onegov.header-resized', function (event) {
    header = document.getElementById('header')

    // Remove height of header from video
    var header_height = $('#header').height();
    var video_wrapper = $('.homepage-video');
    var current_height = video_wrapper.data('max-height');
    var new_height = 'calc(' + current_height + ' - ' + header_height + 'px)';

    video_wrapper.css('max-height', new_height)
}, {once: true})

    // Slider
    if ($('.orbit.slider').length) {
        var orbit_slider = $('.homepage-image-slider .orbit-container');
        var current_mobile_height = orbit_slider.data('height-m');
        var current_desktop_height = orbit_slider.data('height-d');

        if (current_mobile_height || current_desktop_height) {
            if (w.matches) {
                if (current_mobile_height.slice(-2) == "vh") {
                    var new_height = 'calc(' + current_mobile_height + ' - ' + header_height + 'px)';
                } else {
                    var new_height = current_mobile_height;
                }
            } else {
                if (current_desktop_height.slice(-2) == "vh") {
                    var new_height = 'calc(' + current_desktop_height + ' - ' + header_height + 'px)';
                } else {
                    var new_height = current_desktop_height;
                }
            }
            orbit_slider.css('height', new_height);
        } else {
            orbit_slider.css('height', '40vw');
        }

    }


// Find out if we're on desktop or mobile
var w = window.matchMedia("(max-width: 700px)");

// Video
if (document.getElementById("autoplay-video")) {
    if (document.getElementById("random-video")) {
        var parent = document.getElementById("random-video");
        var children = parent.children;

        var count = children.length;
        var keep = Math.floor(Math.random() * count);

        for (let i = 0; i < count-1; i++) {
            if (i < keep) {
                parent.removeChild(children[0]);
            } else {
                parent.removeChild(children[1]);
            }
        }
    }

    // Once only one video remains
    if (document.getElementsByClassName("homepage-video").length) {

        // Resize spacer
        var vid = document.querySelector('#autoplay-video');
        vid.addEventListener('loadeddata', (event) => {
            var ratio = vid.videoHeight / vid.videoWidth * 100;
            var spacer = document.getElementById("spacer");
            spacer.style.paddingBottom = ratio + "%";
        });

        var source = document.createElement("source");
        source.id = "hvid";
        vid.appendChild(source);

        var link_mp4 = vid.dataset.linkMp4;
        var link_mp4_low_res = vid.dataset.linkMp4LowRes;
        var link_webm = vid.dataset.linkWebm;
        var link_webm_low_res = vid.dataset.linkWebmLowRes;

        if (w.matches && (link_mp4_low_res || link_webm_low_res)) {
            vid.pause();
            source.removeAttribute("src");
            source.setAttribute("src", (link_mp4_low_res || link_webm_low_res));
            source.setAttribute("type", 'video/' + (link_mp4_low_res !== '' ? 'mp4' : 'webm'));
            vid.load();
            vid.play();
        } else {
            vid.pause();
            source.removeAttribute("src");
            source.setAttribute("src", (link_mp4 || link_webm));
            source.setAttribute("type", 'video/' + (link_mp4 !== '' ? 'mp4' : 'webm'));
            vid.load();
            vid.play();
        }
    }
}

