/*
    Creates a dropzone which hashes files dropped on it, sends the filename
    and digest to a remote url and displays the resulting html inside a target
    element.

    Currently only SHA256 is supported.

    Example:

    <div class="filedigest dropzone"
        data-filedigest-handler="/my-url"
        data-filedigest-target=".filedigest-results">
    </div>

    <div class="filedigest-results"></div>
*/
var DigestHandler = function(file, handler) {
    return function(e) {
        handler(file, asmCrypto.SHA256.hex(e.target.result));
    };
};

var FileDigest = function(element, handler) {
    var el = $(element);

    el.on('dragenter', function() {
        $(this).toggleClass('drag-over', true);
    });

    el.on('dragleave drop', function() {
        $(this).toggleClass('drag-over', false);
    });

    el.on('dragover', function() {
        return false;
    });

    el.on('drop', function(e) {
        var files = e.originalEvent.dataTransfer.files;

        for (var i = 0; i < files.length; i++) {
            var reader = new FileReader();
            reader.onload = new DigestHandler(files[i], handler);
            reader.readAsArrayBuffer(files[i]);
        }

        return false;
    });
};

jQuery.fn.FileDigest = function() {
    this.each(function() {
        var el = $(this);
        var baseurl = el.data('filedigest-handler');
        var target = el.data('filedigest-target');

        FileDigest($(this), function(file, digest) {
            var url = new Url(baseurl);
            url.query.digest = digest;
            url.query.name = file.name;

            $.get(url.toString(), function(data) {
                $(target).append(data);
            });
        });
    });
};

$(document).ready(function() {
    $('.filedigest').FileDigest();
});
