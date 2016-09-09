$(function() {
    $('textarea[data-editor]').each(function() {
        var textarea = $(this);

        var mode = textarea.data('editor');
        var readonly = textarea.is('[readonly]');
        textarea.css('display', 'none');

        var outside = $('<div class="code-editor-wrapper">');

        var inside = $('<div class="code-editor">');
        inside.position('absolute');

        outside.append(inside);
        outside.insertBefore(textarea);

        var editor = ace.edit(inside[0]);
        editor.setOptions({
            minLines: 10,
            maxLines: 50
        });
        editor.setHighlightActiveLine(false);
        editor.setDisplayIndentGuides(true);
        editor.setFontSize('12px');
        editor.renderer.setPadding(10);
        editor.renderer.setShowGutter(false);
        editor.renderer.setScrollMargin(10, 10, 10, 10);
        editor.getSession().setValue(textarea.val());
        console.log(mode);
        editor.getSession().setMode("ace/mode/" + mode);
        editor.setTheme("ace/theme/tomorrow");

        editor.on("focus", function() {
            inside.toggleClass('focused', true);
            outside.toggleClass('focused', true);
        });
        editor.on("blur", function() {
            inside.toggleClass('focused', false);
            outside.toggleClass('focused', false);
        });

        var highlighted_line = null;

        if (textarea.data('highlight-line')) {
            var Range = ace.require('ace/range').Range;
            var line = textarea.data('highlight-line');

            highlighted_line = editor.getSession().addMarker(
                new Range(line - 1, 0, line - 1, 100000), "ace-syntax-error", "fullLine", false
            );
        }

        if (readonly === true) {
            outside.addClass('read-only');
            inside.addClass('read-only');
            editor.setReadOnly(true);
            editor.setDisplayIndentGuides(false);
            editor.renderer.$cursorLayer.element.style.opacity = 0;
            editor.getSession().setMode("ace/mode/text");
        }

        editor.getSession().on('change', function() {
            if (highlighted_line !== null) {
                editor.getSession().removeMarker(highlighted_line);
                highlighted_line = null;
            }
            textarea.val(editor.getSession().getValue());
        });
    });
});
