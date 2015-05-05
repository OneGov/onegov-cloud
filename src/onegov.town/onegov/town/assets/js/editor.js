$(function() {
    _.each($('textarea.editor'), function(el) {
        var textarea = $(el);
        var form = textarea.closest('form');

        textarea.redactor({
            imageUpload: form.data('image-upload-url'),
            imageManagerJson: form.data('image-list-url'),
            plugins: ['imagemanager']
        });
    });
});
