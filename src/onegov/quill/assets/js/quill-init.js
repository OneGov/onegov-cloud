window.addEventListener('load', function() {
    const widgets = document.querySelectorAll('.quill-widget');
    Array.prototype.slice.call(widgets).forEach(function(widget, _index) {
        const inputId = widget.dataset.inputId;
        const containerId = widget.dataset.containerId;
        const scrollContainerId = widget.dataset.scrollContainerId;
        const formats = JSON.parse(widget.dataset.formats);
        const toolbar = JSON.parse(widget.dataset.toolbar);
        const input = document.getElementById(inputId);

        const quill = new Quill('#' + containerId, {
            formats: formats,
            modules: {toolbar: toolbar},
            scrollingContainer: '#' + scrollContainerId,
            theme: 'snow'
        });
        quill.clipboard.dangerouslyPasteHTML(input.value);
        quill.on('text-change', function() {
            input.value = quill.root.innerHTML;
        });
    });
});
