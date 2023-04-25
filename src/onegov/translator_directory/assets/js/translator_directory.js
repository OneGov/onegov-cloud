// Used in the document search view template
function updateUploadUrl(protected_url) {
    $('form.upload').attr("action", protected_url);
}

const bulk_email_button = document.querySelectorAll('a.button.envelope.tiny')[0];
bulk_email_button.addEventListener('click', function(event) {
    event.preventDefault();
    const href = event.currentTarget.getAttribute('href');
    // could even show the number of recipients in the message
    const message = locale("The circular to translators has been opened in your e-mail software.");
    showAlertMessage(message, 'success');
    window.location.href = href;
});

