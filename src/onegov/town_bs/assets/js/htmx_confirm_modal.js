/*
    Shows a bootstrap modal instead of the native confirm dialog for htmx
    requests. The question is taken from hx-confirm, the modal from
    data-confirm-modal. The modal needs a button with data-confirm-yes.

    <a hx-delete="..."
       hx-confirm="Do you really want to?"
       data-confirm-modal="#my-modal"
       i18n:attributes="hx-confirm">Delete</a>
*/
document.addEventListener('htmx:confirm', function(event) {
    var selector = event.detail.elt.getAttribute('data-confirm-modal');
    if (!selector || !event.detail.question) {
        return;
    }

    var modalEl = document.querySelector(selector);
    if (!modalEl) {
        return;
    }

    event.preventDefault();

    modalEl.querySelector('.modal-body').textContent = event.detail.question;

    var confirmButton = modalEl.querySelector('[data-confirm-yes]');
    var onConfirm = function() {
        event.detail.issueRequest(true);
    };

    confirmButton.addEventListener('click', onConfirm, {once: true});
    modalEl.addEventListener('hidden.bs.modal', function() {
        confirmButton.removeEventListener('click', onConfirm);
    }, {once: true});

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
});

// Elements added with jQuery (e.g. uploaded images) are unknown to htmx
$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).each(function() {
        htmx.process(this);
    });
});
