$(function() {
    _.each($('textarea.editor'), function(el) {
        var textarea = $(el);
        var form = textarea.closest('form');
        var language = window.locale.language;
        var translation = $.Redactor.opts.langs[language];

        textarea.redactor({
            buttons: [
                'formatting', 'bold', 'italic', 'deleted',
                'unorderedlist', 'orderedlist', 'image', 'file', 'link',
                'horizontalrule', 'html'
            ],
            formatting: ['p', 'blockquote', 'pre'],
            fileUpload: form.data('file-upload-url'),
            fileManagerJson: form.data('file-list-url'),
            imageUpload: form.data('image-upload-url'),
            imageManagerJson: form.data('image-list-url'),
            definedLinks: form.data('sitecollection-url'),
            plugins: ['bufferbuttons', 'filemanager', 'imagemanager', 'definedlinks'],
            lang: language,
            convertVideoLinks: false,
            imageResizable: false,
            formattingAdd: [
                {
                    tag: 'h2',
                    title: translation.title
                },
                {
                    tag: 'h3',
                    title: translation.subtitle
                }
            ],
            /* defined in input_with_button.js */
            fileUploadErrorCallback: handleUploadError,
            imageUploadErrorCallback: handleUploadError
        });
    });
});
