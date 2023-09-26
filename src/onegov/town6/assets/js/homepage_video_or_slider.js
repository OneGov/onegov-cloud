var header_height = $('#header').height();

// Video
if (document.getElementById("autoplay-video")) {
    if (document.getElementById("autoplay-video")) {
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

        // Find out if we're on desktop or mobile
        var w = window.matchMedia("(max-width: 700px)");
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

    // Remove height of header from video
    var video_wrapper = $('.homepage-video');
    var current_height = video_wrapper.data('max-height');
    var new_height = 'calc(' + current_height + ' - ' + header_height + 'px)';

    video_wrapper.css('max-height', new_height)
}


// Slider
if ($('.orbit.slider').length) {
    var orbit_slider = $('.orbit-container');
    var current_height = orbit_slider.data('height');
    if (current_height) {
        var new_height = 'calc(' + current_height + ' - ' + header_height + 'px)';
    
        orbit_slider.css('height', new_height);
    }

    // Mol luege
    var smallest_height = 100000000;


    $('.orbit-container .orbit-image').each(function(){
        var url =  $(this).data('image-url');

        var tempImg = '<img id="tempImg" src="' + url + '"/>';
        $('body').append(tempImg); // add to DOM before </body>
        $('#tempImg').hide(); //hide image
        height = $('#tempImg').height(); //get height
        $('#tempImg').remove(); //remove from DOM
        console.log('height', height);

        // image = new Image();

        // // just in case it is not already loaded
        // $(image).load(function () {
        //     alert(image.width + 'x' + image.height);
        // });
    
        // image.src = url;

        console.log('url', url)
    });

    console.log('nochehr?')

}

