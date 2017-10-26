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
        editor.$blockScrolling = 1;
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

        if (mode === 'form') {
            var watcher = formcodeWatcherRegistry.new();

            editor.on("change", _.debounce(function() {
                watcher.update(editor.getValue());
            }, 500));

            var form = textarea.closest('form');
            form.find('.formcode-format').each(function() {
                var container = $("<div>").insertBefore(this);
                initFormcodeFormat(container.get(0), watcher, this);
            });

            $('.formcode-select').each(function() {
                var exclude = (this.getAttribute('data-fields-exclude') || '');
                var include = (this.getAttribute('data-fields-include') || '');
                var container = $("<div>").insertBefore(this);

                $(this).hide();

                initFormcodeSelect(container.get(0), watcher, this, include.split(','), exclude.split(','));
            });
        }

        editor.getSession().setValue(textarea.val());
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

        if (mode === 'form') {
            var fnid = 'onInsertSnippet' + Math.floor(Math.random() * 10001);
            var toolbar = $(
                '<div class="formcode-ace-editor-toolbar" ' +
                     'data-source="/formcode-snippets" ' +
                     'data-target="' + fnid + '">'
            );

            window[fnid] = function(snippet, title) {
                var AceRange = ace.require("ace/range").Range;
                var session = editor.getSession();
                var selection = editor.getSelectionRange();

                // insert before or after the line?
                var insert = selection.end.column === 0 && snippet + '\n' || '\n' + snippet;

                // where to insert?
                var row = editor.getSelectionRange().start.row;
                var column = selection.end.column !== 0 && Number.MAX_VALUE || 0;
                var length = session.getLength();

                // only insert after a line that doesn't begin with a space
                // (skipping over multiline fields)
                if (column > 0) {
                    while (row < length && session.getLine(row + 1)[0] === " ") {
                        row += 1;
                    }
                }

                // set the selection to a single character and insert
                editor.selection.setRange(new AceRange(row, column, row, column));
                session.insert({row: row, column: column}, insert);

                // select the title of the snippet
                editor.selection.setRange(
                    editor.find(title, {
                        range: new AceRange(row, 0, row, Number.MAX_VALUE)
                    })
                );

                editor.focus();
            };

            toolbar.insertBefore(outside);
            initFormSnippets(toolbar.get(0));
        }
    });
});
