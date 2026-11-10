/* A still frame and a play button for uploaded videos embedded in text. */
(function($) {
    'use strict';

    function preview(video) {
        var $video = $(video);
        if ($video.parent().hasClass('video-preview') || video.autoplay) {
            return;
        }

        $video.wrap('<span class="video-preview">');
        var $wrapper = $video.parent();
        var $play = $('<button type="button" class="video-preview-play" hidden>');
        $play.append('<span class="video-preview-icon" aria-hidden="true">');
        $play.append($('<span class="video-preview-label">').text(window.locale('Play video')));
        var $duration = $('<span class="video-preview-duration" aria-hidden="true">');
        $play.append($duration);
        $wrapper.append($play);

        var started = false;
        var previewTime = null;

        function showPreview() {
            if (started || !video.paused || video.error) {
                return;
            }
            video.controls = false;
            $play.prop('hidden', false);
        }

        function showControls() {
            started = true;
            video.controls = true;
            $play.prop('hidden', true);
        }

        function updateDimensions() {
            if (video.videoWidth && video.videoHeight) {
                var ratio = video.videoWidth / video.videoHeight;
                $wrapper.css('width', 'min(100%, ' + (40 * ratio) + 'rem, ' + (70 * ratio) + 'vh)');
            }
        }

        function prepare() {
            updateDimensions();
            if (isFinite(video.duration)) {
                var seconds = Math.floor(video.duration);
                $duration.text(Math.floor(seconds / 60) + ':' + ('0' + seconds % 60).slice(-2));
            }

            // Avoid a black opening frame, while preserving explicit posters
            // and media fragments. Playback still starts at the beginning.
            if (!started && !video.poster && video.currentTime === 0 &&
                    video.duration > 0 && (video.currentSrc || '').indexOf('#t=') === -1) {
                previewTime = Math.min(0.5, video.duration / 2);
                video.currentTime = previewTime;
            } else if (video.poster || video.readyState >= 2) {
                showPreview();
            }
        }

        $video.on('loadedmetadata', prepare);
        $video.on('loadeddata seeked', showPreview);
        $video.on('play error', showControls);

        $play.on('click', function() {
            showControls();
            if (previewTime !== null) {
                video.currentTime = 0;
                previewTime = null;
            }
            video.setAttribute('playsinline', '');
            video.focus();
            var playing = video.play();
            if (playing && playing.catch) {
                playing.catch(function() {
                    // The native controls remain usable if playback fails.
                    showControls();
                });
            }
        });

        if (video.readyState >= 1) {
            prepare();
        }
    }

    $(function() {
        $('.page-text video[controls]').each(function() {
            preview(this);
        });
    });
})(jQuery);
