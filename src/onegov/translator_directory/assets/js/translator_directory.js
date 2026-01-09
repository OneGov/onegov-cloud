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


document.addEventListener("DOMContentLoaded", function() {
    moveMailTemplateButtonToEnd();

    // Auto-submit time reports filter form when month or year changes
    $('#time-reports-filter select[name="month"], #time-reports-filter select[name="year"]').on('change', function() {
        $(this).closest('form').submit();
    });
});
