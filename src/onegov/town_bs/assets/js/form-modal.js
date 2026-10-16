document.addEventListener('DOMContentLoaded', function() {
    var params = new URLSearchParams(window.location.search);
    var formName = params.get('form');
    var submissionUrl = params.get('submission');

    // Open modal if form name is in parameters
    if (formName) {
        var link = document.querySelector(
            '[data-form-name="' + CSS.escape(formName) + '"]'
        );

        if (link) {
            var modalUrl = submissionUrl || link.getAttribute('hx-get');
            var requestOptions = { target: '#form-modal-body' };
            if (submissionUrl) {
                requestOptions.select = '#content > *';
            }

            htmx.ajax('GET', modalUrl, requestOptions).then(function() {
                var modalEl = document.getElementById('form-modal');
                var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
            });
        }
    }

    // Delete form parameter when modal is being closed
    var formModal = document.getElementById('form-modal');
    formModal.addEventListener('hidden.bs.modal', function() {
        var url = new URL(window.location.href);
        if (url.searchParams.has('form')) {
            url.searchParams.delete('form');
            url.searchParams.delete('submission');
            window.history.pushState({}, '', url.pathname + url.search);
        }
        document.getElementById('form-modal-body').innerHTML = '';
    });
});