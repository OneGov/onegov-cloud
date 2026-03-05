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


function setupAutoEndDate() {
    const startDateField = document.querySelector('input[name="start_date"]');
    const endDateField = document.querySelector('input[name="end_date"]');
    if (!startDateField || !endDateField) { return; }
    startDateField.addEventListener('change', function() {
        endDateField.value = startDateField.value;
    });
}


function setupTimeReportForm() {

    // check if we are on the desired page, else don't run
    const assignmentTypeField = document.querySelector(
        'select[name="assignment_type"]'
    );
    if (!assignmentTypeField) { return; }

    setupAutoEndDate();

    const timeOnlyFields = [
        'start_time', 'end_date', 'end_time', 'break_time', 'is_urgent'
    ];

    const startDateLabel = document.querySelector(
        '.field-start_date .label-text'
    );
    const startDateOriginalLabel = startDateLabel
        ? startDateLabel.textContent : null;

    function updateTimeFields() {
        const isSchriftlich = assignmentTypeField.value === 'schriftlich';
        if (startDateLabel && startDateOriginalLabel) {
            startDateLabel.textContent = isSchriftlich
                ? 'Datum' : startDateOriginalLabel;
        }
        const pagesLabel = document.querySelector('.field-pages .label-text');
        if (pagesLabel) {
            const existing = pagesLabel.parentElement.querySelector(
                '.label-required'
            );
            if (isSchriftlich && !existing) {
                const star = document.createElement('span');
                star.className = 'label-required';
                star.textContent = '*';
                pagesLabel.insertAdjacentElement('afterend', star);
            } else if (!isSchriftlich && existing) {
                existing.remove();
            }
        }
        timeOnlyFields.forEach(function(name) {
            const wrapper = document.querySelector('.field-' + name);
            const input = document.querySelector('[name="' + name + '"]');
            if (wrapper) {
                wrapper.style.display = isSchriftlich ? 'none' : '';
            }
            if (input) {
                input.required = !isSchriftlich;
            }
        });
        const pagesInput = document.querySelector('[name="pages"]');
        if (pagesInput) {
            pagesInput.required = isSchriftlich;
        }
    }

    $(document).on('change', 'select[name="assignment_type"]', updateTimeFields);
    updateTimeFields();
}


document.addEventListener("DOMContentLoaded", function() {
    moveMailTemplateButtonToEnd();
    setupTimeReportForm();
});
