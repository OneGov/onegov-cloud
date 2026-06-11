var translation = $.Redactor.opts.langs[language];

(function($) {
    $.Redactor.prototype.superscript = function() {
        return {
            init: function() {
                var button = this.button.add('superscript', translation.superscript);
                this.button.addCallback(button, this.superscript.format);
                button.html('x<sup>2</sup>')
            },
            format: function() {
                this.inline.format('sup');
            }
        };
    };
})(jQuery);

(function($) {
    $.Redactor.prototype.subscript = function() {
        return {
            init: function() {
                var button = this.button.add('subscript', translation.subscript);
                this.button.addCallback(button, this.subscript.format);
                button.html('x<sub>2</sub>')
            },
            format: function() {
                this.inline.format('sub');
            }
        };
    };
})(jQuery);

$(function() {
    _.each($('textarea.editor'), function(el) {
        var textarea = $(el);
        var form = textarea.closest('form');
        var language = window.locale.language;

        textarea.redactor({
            buttons: [
                'formatting', 'bold', 'italic', 'deleted',
                'unorderedlist', 'orderedlist', 'alphalist', 'image', 'file',
                 'link', 'horizontalrule', 'html', 'superscript', 'subscript'
            ],
            formatting: ['p', 'blockquote', 'pre'],
            fileUpload: form.data('file-upload-url'),
            fileManagerJson: form.data('file-list-url'),
            imageUpload: form.data('image-upload-url'),
            imageManagerJson: form.data('image-list-url'),
            definedLinks: form.data('sitecollection-url'),
            plugins: ['alphalist', 'bufferbuttons', 'filemanager', 'imagemanager', 'definedlinks', 'table', 'superscript', 'subscript'],
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
                },
                {
                    tag: 'h4',
                    title: translation.subsubtitle
                },
                {
                    tag: 'h5',
                    title: translation.subsubsubtitle
                },
                {
                    tag: 'p',
                    class: 'edit-note',
                    title: translation.editnote
                }
            ],
            /* defined in input_with_button.js */
            fileUploadErrorCallback: handleUploadError,
            imageUploadErrorCallback: handleUploadError
        });
    });
});
