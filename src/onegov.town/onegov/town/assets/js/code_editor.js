$(function () {
    $('textarea[data-editor]').each(function () {
        var textarea = $(this);

        var mode = textarea.data('editor');
        var readonly = textarea.is('[readonly]');

        var height = textarea.height();
        var width = textarea.width();

        var wrapper = $('<div class="code-editor-wrapper">');
        wrapper.position('absolute');
        wrapper.height(textarea.height());
        wrapper.insertBefore(textarea);

        var editor = ace.edit(wrapper[0]);
        editor.setHighlightActiveLine(false);
        editor.setDisplayIndentGuides(true);
        editor.renderer.setShowGutter(false);
        editor.getSession().setValue(textarea.val());
        editor.getSession().setMode("ace/mode/" + mode);
        editor.setTheme("ace/theme/clouds");

        if (readonly === true) {
            wrapper.addClass('read-only');
            editor.setReadOnly(true);
            editor.setDisplayIndentGuides(false);
            editor.renderer.$cursorLayer.element.style.opacity=0;
            editor.getSession().setMode("ace/mode/text");
        }

        editor.getSession().on('change', function(){
            textarea.val(editor.getSession().getValue());
        });

        textarea.css('display', 'none');
    });
});
