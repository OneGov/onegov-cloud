document.addEventListener("DOMContentLoaded", function () {
    handleBulkAddCommission();
    handleAttendanceFormSync();
});


function handleBulkAddCommission() {

  const commissionSelect = document.getElementById("commission_id");
  const parliamentarianList = document.getElementById("parliamentarian_id");

  // Store all parliamentarians by commission
  let commissionParliamentarians = {};
  let isInitialLoad = true;
  const baseUrl = window.location.href.split("/").slice(0, -2).join("/");
  fetch(`${baseUrl}/commissions/commissions-parliamentarians-json`)
    .then((response) => response.json())
    .then((data) => {
      commissionParliamentarians = data;
      // Initial update based on selected commission
      updateParliamentarians(commissionSelect.value);
      isInitialLoad = false;
    })
    .catch(error => {
      console.error("DEBUG: Fetch error:", error);
    });

  // NOTE: The "chosen" library is a jQuery plugin. It hides the original
  // <select> element and creates a custom, styled dropdown. When we make a
  // selection, the plugin triggers a change event on the original, hidden
  // element using jQuery's internal event system. A vanilla JavaScript
  // attempt (addEventListener, event delegation) won't cut it here.
  $(commissionSelect).on("change", function () {
    updateParliamentarians(this.value);
  });

  function updateParliamentarians(commissionId) {

    // Hide all existing checkboxes first
    const allCheckboxes = parliamentarianList.querySelectorAll('li');

    allCheckboxes.forEach(li => {
      li.style.display = 'none';
      const checkbox = li.querySelector('input[type="checkbox"]');
      if (checkbox) {
        checkbox.checked = false;
      }
    });

    if (!commissionId) {
      return;
    }

    const parliamentarians = commissionParliamentarians[commissionId] || [];

    parliamentarians.forEach((parliamentarian) => {
      // Find the existing checkbox for this parliamentarian
      const existingCheckbox = parliamentarianList.querySelector(`input[value="${parliamentarian.id}"]`);

      if (existingCheckbox) {
        const li = existingCheckbox.closest('li');
        if (li) {
          li.style.display = 'block';
          existingCheckbox.checked = true;
          if (!isInitialLoad) {
            li.classList.add("animate-in");
          }
        }
      }
    });
  }
}


function handleAttendanceFormSync() {
  const commissionSelect = document.getElementById("commission_id");
  const parliamentarianSelect = document.getElementById("parliamentarian_id");

  // Only proceed if both elements exist (not all forms have both)
  if (!commissionSelect || !parliamentarianSelect) {
    return;
  }

  // Store all parliamentarians by commission
  let commissionParliamentarians = {};
  let parliamentarianCommissions = {};
  const baseUrl = window.location.href.split("/").slice(0, -2).join("/");


  fetch(`${baseUrl}/commissions/commissions-parliamentarians-json`)
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      commissionParliamentarians = data;

      // Build reverse mapping: parliamentarian -> commissions
      Object.keys(data).forEach(commissionId => {
        data[commissionId].forEach(parliamentarian => {
          if (!parliamentarianCommissions[parliamentarian.id]) {
            parliamentarianCommissions[parliamentarian.id] = [];
          }
          parliamentarianCommissions[parliamentarian.id].push(commissionId);
        });
      });
    })
    .catch(error => {
      console.error("DEBUG: Fetch error:", error);
    });

  // Commission change -> filter parliamentarians
  $(commissionSelect).on("change", function () {
    filterParliamentariansByCommission(this.value);
  });

  // Parliamentarian change -> filter commissions
  $(parliamentarianSelect).on("change", function () {
    filterCommissionsByParliamentarian(this.value);
  });

  function filterParliamentariansByCommission(commissionId) {
    const parliamentarianOptions = parliamentarianSelect.querySelectorAll('option');

    // Reset all options to visible
    parliamentarianOptions.forEach(option => {
      option.style.display = '';
      option.disabled = false;
    });

    if (!commissionId) {
      // Update chosen dropdown
      $(parliamentarianSelect).trigger('chosen:updated');
      return;
    }

    const validParliamentarians = commissionParliamentarians[commissionId] || [];
    const validIds = validParliamentarians.map(p => p.id.toString());

    parliamentarianOptions.forEach(option => {
      if (option.value && !validIds.includes(option.value)) {
        option.style.display = 'none';
        option.disabled = true;
        // Unselect if currently selected
        if (option.selected) {
          option.selected = false;
        }
      }
    });

    // Update chosen dropdown
    $(parliamentarianSelect).trigger('chosen:updated');
  }

  function filterCommissionsByParliamentarian(parliamentarianId) {
    const commissionOptions = commissionSelect.querySelectorAll('option');

    // Reset all options to visible
    commissionOptions.forEach(option => {
      option.style.display = '';
      option.disabled = false;
    });

    if (!parliamentarianId) {
      // Update chosen dropdown
      $(commissionSelect).trigger('chosen:updated');
      return;
    }

    const validCommissions = parliamentarianCommissions[parliamentarianId] || [];

    commissionOptions.forEach(option => {
      if (option.value && !validCommissions.includes(option.value)) {
        option.style.display = 'none';
        option.disabled = true;
        // Unselect if currently selected
        if (option.selected) {
          option.selected = false;
        }
      }
    });

    // Update chosen dropdown
    $(commissionSelect).trigger('chosen:updated');
  }
}

function handleImportButton() {

    if (!window.location.href.includes('/import-logs')) {
        return
    }
    document.addEventListener('DOMContentLoaded', function() {
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
    });
}
