$(function() {
    _.each($('textarea.editor'), function(el) {
        var textarea = $(el);
        var form = textarea.closest('form');

        textarea.redactor({
            buttons: ['bold', 'italic'],
            formatting: ['p', 'blockquote'],
            lang: 'de',
        });
    });
});
