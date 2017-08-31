$(function() {
    $('input.quill').each(function() {
        var input = $(this);
        var container = input.prev('.quill-container');
        var form = input.closest('form');
        var quill = new Quill(container.get(0), {
            formats: ['bold', 'italic', 'list'],
            modules: {
                toolbar: [
                    'bold', 'italic', {list: 'ordered'}, {list: 'bullet'}
                ]
            },
            theme: 'snow'
        });
        quill.clipboard.dangerouslyPasteHTML(input.val());
        form.submit(function() {
            input.val(quill.root.innerHTML);
        });
    });
});
