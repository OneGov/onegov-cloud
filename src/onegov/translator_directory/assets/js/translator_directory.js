function updateUploadUrl(protected_url) {
    $('form.upload').attr("action", protected_url);
}
