// Used in the document search view template
function updateUploadUrl(protected_url) {
    $('form.upload').attr("action", protected_url);
}

$("#select-category").on("change", function() {
    window.location = this.value;
});
