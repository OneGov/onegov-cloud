// Used in the document search view template
function updateUploadUrl(protected_url) {
    $('form.upload').attr("action", protected_url);
}
