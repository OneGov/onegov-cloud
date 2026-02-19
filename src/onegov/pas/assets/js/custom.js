document.addEventListener("DOMContentLoaded", function () {
    handleBulkAddCommission();
    handleAttendanceFormSync();
    handleParliamentarianCounter();
});


function handleBulkAddCommission() {
    // Sync the displayed parliamentarian checkboxes with the selected
    // commission. Hides checkboxes for parliamentarians not in the
    // commission.

   if (!window.location.href.includes('new-commission-bulk')) {
        return;
    }

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
      // Filter commission options to only show those with parliamentarians
      filterCommissionOptions();
      // Initial update based on selected commission
      if (commissionSelect.value) {
        updateParliamentarians(commissionSelect.value);
      }
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

  function filterCommissionOptions() {
    // Hide commission options that have no parliamentarians
    const commissionOptions = commissionSelect.querySelectorAll('option');
    let firstValidCommission = null;

    commissionOptions.forEach(option => {
      // Skip the empty/placeholder option
      if (!option.value) {
        return;
      }

      const commissionId = option.value;
      const parliamentarians = commissionParliamentarians[commissionId] || [];

      // Hide commissions with no parliamentarians
      if (parliamentarians.length === 0) {
        option.style.display = 'none';
        option.disabled = true;
      } else if (!firstValidCommission) {
        firstValidCommission = commissionId;
      }
    });

    // If the selected commission is not in the data, default to first valid
    if (commissionSelect.value && !commissionParliamentarians[commissionSelect.value]) {
      commissionSelect.value = firstValidCommission || '';
    }

    // Update the chosen dropdown to reflect changes
    $(commissionSelect).trigger('chosen:updated');
  }

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


function handleParliamentarianCounter() {
    if (!window.location.href.includes('/new-bulk')) {
        return;
    }

    var $list = $('#parliamentarian_id');
    if (!$list.length || !$list.is('ul')) {
        return;
    }

    var $counter = $('<li><strong></strong></li>');
    $list.prepend($counter);

    function update() {
        var $boxes = $list.find("input[type='checkbox']");
        var total = $boxes.length;
        var checked = $boxes.filter(':checked').length;
        $counter.find('strong').text(checked + ' / ' + total);
    }

    update();
    $list.on('change', 'input[type="checkbox"]', update);
}


function handleAttendanceFormSync() {
    // Pre-restrict interdependent dropdown values to prevent invalid
    // combinations. When a user selects a commission or parliamentarian,
    // the other dropdown dynamically filters to show only valid pairings.
    // This improves UX by preventing form submissions with mismatched
    // selections and making the valid options immediately clear.

    // Applies to *single* attendance form only.
   if (!window.location.href.includes('attendences/new')) {
        return;
    }

  const commissionSelect = document.getElementById("commission_id");
  const parliamentarianSelect = document.getElementById("parliamentarian_id");

  // Only proceed if both elements exist (not all forms have both)
  if (!commissionSelect || !parliamentarianSelect) {
    return;
  }

  // Store commission->parliamentarians and parliamentarian->commissions
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
