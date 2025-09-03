document.addEventListener("DOMContentLoaded", function () {
    handleBulkAddCommission();
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
