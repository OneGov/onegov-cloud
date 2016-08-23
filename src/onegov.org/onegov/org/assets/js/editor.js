$(function() {
    _.each($('textarea.editor'), function(el) {
        var textarea = $(el);
        var form = textarea.closest('form');

        textarea.redactor({
            buttons: [
                'formatting', 'bold', 'italic', 'deleted',
                'unorderedlist', 'orderedlist', 'image', 'file', 'link',
                'horizontalrule', 'html'
            ],
            formatting: ['p', 'blockquote'],
            fileUpload: form.data('file-upload-url'),
            fileManagerJson: form.data('file-list-url'),
            imageUpload: form.data('image-upload-url'),
            imageManagerJson: form.data('image-list-url'),
            definedLinks: form.data('sitecollection-url'),
            plugins: ['bufferbuttons', 'filemanager', 'imagemanager', 'definedlinks'],
            lang: 'de',
            convertVideoLinks: false,
            formattingAdd: [
                {
                    tag: 'h2',
                    title: "Titel"
                },
                {
                    tag: 'h3',
                    title: "Untertitel"
                }
            ],
            /* defined in input_with_button.js */
            fileUploadErrorCallback: handleUploadError,
            imageUploadErrorCallback: handleUploadError
        });
    });
});
