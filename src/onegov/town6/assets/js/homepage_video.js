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
    if (document.getElementsByClassName("homepage-video").length ==1) {
    
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
    
        var link_mp4 = vid.dataset.linkMp4
        var link_mp4_low_res = vid.dataset.linkMp4LowRes
        var link_webm = vid.dataset.linkWebm
        var link_webm_low_res = vid.dataset.linkWebmLowRes
        
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
