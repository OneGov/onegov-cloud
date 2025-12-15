/*
    Provides a minimal HTML 5 upload automatically enabled on the following
    html structure:

    <form class='upload' action="upload-url" method="POST" enctype="multipart/form-data">
        <div class="upload-dropzone dropzone" />
        <div class="upload-progress" />
        <div class="upload-filelist-header" />
        <div class="upload-filelist" />

        <noscript>
            <input name="file" type="file" multiple />
            <input type="submit" value="Submit">
        </noscript>
    </div>

    When files are dropped on the dropzone, a <progress> element is added
    at the top of the file list for each file being uploaded.

    Once the upload is done, the progress bar is replaced with the html
    response of the upload handler (the upload handler should return an
    html fragment to the effect).

    See http://archive.is/3m5s8
*/
var Upload = function(element) {
    var url = element.attr('action');

    var dropzone = $(element.find('.upload-dropzone'));
    var drop_button = $(element.find('#fileElem'));
    var progress = $(element.find('.upload-progress'));
    var filelist = $(element.find('.upload-filelist'));
    var filelist_header = $(element.find('.upload-filelist-header'));

    var upload_queue = [];
    var pending_upload = false;

    var upload = function(file, bar) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);

        var data = new FormData();
        data.append('file', file);
        data.append('file_type', file.type);

        xhr.upload.addEventListener('progress', function(e) {
            bar.find('.meter').css('width', (e.loaded / e.total * 100 || 100) + '%');
        });

        xhr.addEventListener('readystatechange', function() {
            if (xhr.readyState !== 4) {
                return;
            }

            pending_upload = false;

            if (xhr.status === 200) {
                bar.remove();
                filelist_header.show();

                if (xhr.responseText.length !== 0) {
                    processCommonNodes($(xhr.responseText).appendTo(filelist), true);
                }
            } else if (xhr.status === 415){  // Unsupported media type
                // reload page in order to show the request error message
                window.location.reload();
                return;
            } else {
                bar.find('.meter').css('width', '100%');
                bar.addClass('alert').attr('data-error', xhr.statusText);
            }

            // eslint-disable-next-line no-use-before-define
            process_upload_queue();
        });

        xhr.send(data);
    };

    var process_upload_queue = function() {
        if (pending_upload || upload_queue.length === 0) {
            return;
        }

        var data = upload_queue.shift();
        upload(data.file, data.bar);
    };

    var queue_upload = function(file) {
        var bar = $('<div class="progress"><span class="meter" style="width: 0%"></span></div>')
            .attr('data-filename', file.name)
            .prependTo(progress);
        upload_queue.push({file: file, bar: bar});
    };

    dropzone.on('dragenter', function() {
        $(this).toggleClass('drag-over', true);
    });

    dropzone.on('dragleave drop', function() {
        $(this).toggleClass('drag-over', false);
    });

    dropzone.on('dragover', function() {
        return false;
    });

    dropzone.on('drop', function(e) {
        var files = e.originalEvent.dataTransfer.files;

        for (var i = 0; i < files.length; i++) {
            queue_upload(files[i]);
        }
        process_upload_queue();
        return false;
    });

    drop_button.on('change', function() {
        var files = this.files;

        for (var i = 0; i < files.length; i++) {
            queue_upload(files[i]);
        }
        process_upload_queue();
    });
};

jQuery.fn.Upload = function() {
    this.each(function() {
        Upload($(this));
    });
};

$(document).ready(function() {
    $('.upload').Upload();
});
