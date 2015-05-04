$(function() {
    _.each($('textarea.editor'), function(el) {
        var textarea = $(el);

        textarea.redactor({
            imageUpload: textarea.closest('form').data('image-upload-url')
        });
    });
});
