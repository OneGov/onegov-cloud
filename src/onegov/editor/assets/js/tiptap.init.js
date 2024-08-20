$(function() {
    $('textarea.editor-tiptap').each(function() {
        var textarea = $(this);
        var container = $('<div></div>');
        textarea.after(container);
        textarea.hide();

        const editor = new tiptap.Editor({
            element: container[0],
            extensions: [
                tiptap.StarterKit,
                tiptap.BubbleMenu
            ],
            content: textarea.val(),
            onUpdate: function() {
                textarea.val(editor.getHTML());
            }
        });
    });
});

