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

    // Auto-set end date to match start date in time report form for convenience while typing
    const startDateField = document.querySelector(
        'input[name="start_date"]'
    );
    const endDateField = document.querySelector('input[name="end_date"]');

    if (startDateField && endDateField) {
        startDateField.addEventListener('change', function() {
            endDateField.value = startDateField.value;
        });
    }
});
