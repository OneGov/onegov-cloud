$(document).ready(function() {
    $('.modal.onload').modal('show');

    $('#form-modal').on('hidden.bs.modal', function() {
        var url = new URL(window.location.href);
        if (url.searchParams.has('form')) {
            url.searchParams.delete('form');
            window.history.pushState({}, '', url.pathname + url.search);
        }
        $('#form-modal-body').empty();
    });
});