/*
    Adds a video button to the editor, which lets the user upload a video or
    select one of the uploaded videos and inserts it as an html5 video player.

    Expects the following redactor options:

    * videoUpload, the url to which the video is uploaded, returns the
      same json as the file upload ({filelink, filename} or {error, message})

    * videoManagerJson, the url which returns the uploaded videos, grouped
      by date ([{group, videos: [{title, video}]}])
*/
(function($) {
    var escapeAttribute = function(value) {
        return $('<div>').text(value || '').html().replace(/"/g, '&quot;');
    };

    $.Redactor.prototype.videomanager = function() {
        return {
            init: function() {
                if (!this.opts.videoUpload || !this.opts.videoManagerJson) {
                    return;
                }

                this.modal.addTemplate('videomanager', String() +
                    '<section id="redactor-modal-video-insert">' +
                        '<div id="redactor-modal-video-droparea"></div>' +
                    '</section>'
                );

                var button = this.button.addAfter('image', 'video', window.locale('Video'));
                this.button.addCallback(button, this.videomanager.show);

                this.videomanager.setupSelection();
            },
            /*
                Clicking a video plays it in some browsers (e.g. Firefox),
                instead of placing the cursor next to it. So it can't be
                removed reliably with the keyboard. Instead, we select the
                video on click and show a button to remove it. Backspace and
                delete remove the selected video as well.

                The selection is shown as an overlay, so it never becomes part
                of the content.
            */
            setupSelection: function() {
                this.videomanager.$selected = null;
                this.videomanager.$overlay = $('<div class="redactor-video-overlay">').hide();

                var $remove = $('<button type="button" class="redactor-video-remove">')
                    .text(window.locale('Remove video'))
                    .on('mousedown', function(e) { e.preventDefault(); })
                    .on('click', $.proxy(function(e) {
                        e.preventDefault();
                        this.videomanager.remove();
                    }, this));

                this.videomanager.$overlay.append($remove);
                this.$box.css('position', 'relative').append(this.videomanager.$overlay);

                var box = this.$box[0];
                var editor = this.$editor[0];

                // NOTE: The videos in the editor don't receive any mouse
                //       events (pointer-events: none), since Firefox doesn't
                //       pass them on from its video controls. So we look for
                //       the video at the position of the click instead.
                var videoAt = function(x, y) {
                    var found = null;
                    $(editor).find('video').each(function() {
                        var rect = this.getBoundingClientRect();
                        if (
                            x >= rect.left && x <= rect.right &&
                            y >= rect.top && y <= rect.bottom
                        ) {
                            found = this;
                            return false;
                        }
                        return true;
                    });
                    return found;
                };

                // capture the events before the browser or redactor handle them
                box.addEventListener('mousedown', $.proxy(function(e) {
                    if ($(e.target).closest('.redactor-video-overlay').length) {
                        return;
                    }
                    var video = editor.contains(e.target) && videoAt(e.clientX, e.clientY);
                    if (video) {
                        e.preventDefault();
                        this.videomanager.selectVideo($(video));
                    } else {
                        this.videomanager.deselect();
                    }
                }, this), true);

                var handledKey = null;

                box.addEventListener('keydown', $.proxy(function(e) {
                    if (!this.videomanager.$selected) {
                        return;
                    }
                    if (e.key === 'Backspace' || e.key === 'Delete') {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                        handledKey = e.key;
                        this.videomanager.remove();
                    } else {
                        this.videomanager.deselect();
                    }
                }, this), true);

                // redactor would otherwise process the key again on keyup
                // (e.g. remove the whole paragraph)
                box.addEventListener('keyup', function(e) {
                    if (handledKey !== null && e.key === handledKey) {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                        handledKey = null;
                    }
                }, true);

                $(window).on('resize', $.proxy(this.videomanager.position, this));
            },
            selectVideo: function($video) {
                this.videomanager.$selected = $video;
                this.$editor.focus();
                this.videomanager.position();
                this.videomanager.$overlay.show();
            },
            deselect: function() {
                this.videomanager.$selected = null;
                this.videomanager.$overlay.hide();
            },
            position: function() {
                var $video = this.videomanager.$selected;
                if (!$video) {
                    return;
                }

                var video = $video.offset();
                var box = this.$box.offset();
                this.videomanager.$overlay.css({
                    top: video.top - box.top,
                    left: video.left - box.left,
                    width: $video.outerWidth(),
                    height: $video.outerHeight()
                });
            },
            remove: function() {
                var $video = this.videomanager.$selected;
                if (!$video) {
                    return;
                }

                var $paragraph = $video.parent('p');
                var $next = $paragraph.length ? $paragraph.next() : $();
                $video.remove();

                // remove the paragraph which only contained the video
                var isEmpty = function($element) {
                    return (
                        $element.find('video, img, iframe').length === 0 &&
                        $.trim($element.text().replace(/\u200B/g, '')) === ''
                    );
                };
                if ($paragraph.length && isEmpty($paragraph)) {
                    $paragraph.remove();
                    $paragraph = $();
                }

                this.videomanager.deselect();

                // place the cursor where the video was
                this.$editor.focus();
                if ($paragraph.length) {
                    this.caret.setEnd($paragraph[0]);
                } else if ($next.length) {
                    this.caret.setStart($next[0]);
                } else {
                    this.focus.setEnd();
                }

                this.code.sync();
            },
            show: function() {
                this.modal.load('videomanager', window.locale('Video'), 700);
                this.upload.init(
                    '#redactor-modal-video-droparea',
                    this.opts.videoUpload,
                    this.videomanager.uploaded
                );

                var $modal = this.modal.getModal();
                this.modal.createTabber($modal);
                this.modal.addTab(1, window.locale('Upload'), 'active');
                this.modal.addTab(2, window.locale('Select'));

                $('#redactor-modal-video-droparea').addClass('redactor-tab redactor-tab1');

                var $box = $('<div id="redactor-video-manager-box" class="redactor-tab redactor-tab2">').hide();
                $modal.append($box);

                $.ajax({
                    dataType: 'json',
                    cache: false,
                    url: this.opts.videoManagerJson,
                    success: $.proxy(function(data) {
                        if (data.length === 0) {
                            $box.append($('<p>').text(window.locale('No videos uploaded yet')));
                            return;
                        }

                        $.each(data, $.proxy(function(_key, group) {
                            $box.append($('<p class="redactor-video-manager-group">').text(group.group));

                            var $grid = $('<div class="redactor-video-manager-grid">');
                            $.each(group.videos, $.proxy(function(_index, video) {
                                $grid.append(this.videomanager.preview(video));
                            }, this));
                            $box.append($grid);
                        }, this));
                    }, this)
                });

                this.selection.save();
                this.modal.show();
            },
            /*
                A tile with the first frame of the video, which plays the
                video (muted) while hovering it. A click inserts the video.
            */
            preview: function(video) {
                var $link = $('<a href="#" class="redactor-video-manager-link">')
                    .attr('data-video', video.video)
                    .attr('data-title', video.title)
                    .attr('title', video.title);

                // the media fragment shows a frame shortly after the start,
                // the very first frame is often black
                var $video = $('<video muted playsinline loop preload="metadata">')
                    .attr('src', video.video + '#t=0.5');
                var player = $video[0];
                player.muted = true;

                $link.append($video);
                $link.append($('<span class="redactor-video-manager-title">').text(video.title));

                $link.on('mouseenter focus', function() {
                    var playing = player.play();
                    if (playing && playing.catch) {
                        playing.catch(function() {});
                    }
                });
                $link.on('mouseleave blur', function() {
                    player.pause();
                    player.currentTime = 0.5;
                });
                $link.on('click', $.proxy(this.videomanager.select, this));

                return $link;
            },
            select: function(e) {
                e.preventDefault();
                var $link = $(e.target).closest('.redactor-video-manager-link');
                this.videomanager.insert($link.attr('data-video'), $link.attr('data-title'));
            },
            uploaded: function(json) {
                if (typeof json.error !== 'undefined') {
                    this.modal.close();
                    this.selection.restore();
                    this.core.setCallback('fileUploadError', json);
                    return;
                }

                this.videomanager.insert(json.filelink, json.filename);
            },
            insert: function(url, title) {
                this.modal.close();
                this.selection.restore();
                this.insert.html(
                    '<p><video controls preload="metadata" src="' + escapeAttribute(url) + '"' +
                    ' title="' + escapeAttribute(title) + '"></video></p>'
                );
                this.code.sync();
            }
        };
    };
})(jQuery);
