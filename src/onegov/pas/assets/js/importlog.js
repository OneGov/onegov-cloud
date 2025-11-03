document.addEventListener('DOMContentLoaded', function () {
    handleLogFilters();
    handleImportButton();
});

function handleLogFilters() {

    if (!window.location.href.includes('/import-log/')) {
        return;
    }
    console.log('importlog');

    const filterButtons = document.querySelectorAll('.log-filter');
    const logEntries = document.querySelectorAll('.log-entry');

    if (!filterButtons.length || !logEntries.length) {
        return;
    }

    filterButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const selectedLevel = this.getAttribute('data-level');

            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Filter log entries
            logEntries.forEach(entry => {
                const entryLevel = entry.getAttribute('data-level');

                if (selectedLevel === 'all' || entryLevel === selectedLevel) {
                    entry.style.display = 'block';
                } else {
                    entry.style.display = 'none';
                }
            });
        });
    });
}


function handleImportButton() {
    if (!window.location.href.includes('/import-logs')) {
        return;
    }

    const triggerBtn = document.getElementById('trigger-import-btn');
    if (triggerBtn) {
        // Store original text
        const originalText = triggerBtn.textContent;

        // Listen for intercooler requests
        triggerBtn.addEventListener('beforeSend.ic', function() {
            // Disable button and change text
            triggerBtn.disabled = true;
            triggerBtn.textContent = triggerBtn.dataset.importStartedText;
            triggerBtn.classList.add('disabled');

            // Auto-refresh after 30 seconds
            setTimeout(function() {
                window.location.reload();
            }, 30000);
        });

        // Handle errors - restore button
        triggerBtn.addEventListener('error.ic', function() {
            triggerBtn.disabled = false;
            triggerBtn.textContent = originalText;
            triggerBtn.classList.remove('disabled');
        });
    }
}
