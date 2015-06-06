$(function () {
    $('textarea[data-editor]').each(function () {
        var textarea = $(this);

        var mode = textarea.data('editor');
        var readonly = textarea.is('[readonly]');

        var height = textarea.height();
        var width = textarea.width();
        textarea.css('display', 'none');

        var outside = $('<div class="code-editor-wrapper">');

        var inside = $('<div class="code-editor">');
        inside.position('absolute');

        outside.append(inside);
        outside.insertBefore(textarea);

        var editor = ace.edit(inside[0]);
        editor.setHighlightActiveLine(false);
        editor.setDisplayIndentGuides(true);
        editor.setFontSize('12px');
        editor.renderer.setPadding(0);
        editor.renderer.setShowGutter(false);
        editor.getSession().setValue(textarea.val());
        editor.getSession().setMode("ace/mode/" + mode);
        editor.setTheme("ace/theme/tomorrow");

        if (readonly === true) {
            outside.addClass('read-only');
            inside.addClass('read-only');
            editor.setReadOnly(true);
            editor.setDisplayIndentGuides(false);
            editor.renderer.$cursorLayer.element.style.opacity=0;
            editor.getSession().setMode("ace/mode/text");
        }

        editor.getSession().on('change', function(){
            textarea.val(editor.getSession().getValue());
        });
    });
});
