document.addEventListener('DOMContentLoaded', function() {
    var params = new URLSearchParams(window.location.search);
    var formName = params.get('form');

    if (formName) {
        var link = document.querySelector(
            '.list-link[data-form-name="' + CSS.escape(formName) + '"]'
        );

        if (link) {
            var modalUrl = link.getAttribute('hx-get');

            htmx.ajax('GET', modalUrl, '#form-modal-body').then(function() {
                var modalEl = document.getElementById('form-modal');
                var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
            });
        }
    }

    var formModal = document.getElementById('form-modal');
    formModal.addEventListener('hidden.bs.modal', function() {
        var url = new URL(window.location.href);
        if (url.searchParams.has('form')) {
            url.searchParams.delete('form');
            window.history.pushState({}, '', url.pathname + url.search);
        }
        document.getElementById('form-modal-body').innerHTML = '';
    });
});