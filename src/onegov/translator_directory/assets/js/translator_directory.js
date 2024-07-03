// Used in the document search view template
function updateUploadUrl(protected_url) {
    $('form.upload').attr("action", protected_url);
}

$("#select-category").on("change", function() {
    window.location = this.value;
});

function moveMailTemplateButtonToEnd() {
    const editBar = document.querySelector(".edit-bar");
    if (!window.location.href.includes("/ticket") || (editBar === null)) { return; }

    const mailTemplateButton = editBar.querySelector(".envelope.button.tiny");
    if (mailTemplateButton) {
        editBar.removeChild(mailTemplateButton);
        editBar.appendChild(mailTemplateButton);
    }
}

// fixes tab title containing html
if (document.body.id.startsWith("page-translator-")) {
    if (/div class="adjust-font">.*<\/div>/.test(document.title)) {
        document.title = document.title.replace(/<div class="adjust-font">(.*)<\/div>/, '$1');
    }
}

document.addEventListener("DOMContentLoaded", function() {
    moveMailTemplateButtonToEnd();
});
