document.addEventListener('DOMContentLoaded', function() {

    const commissionSelect = document.getElementById('commission_id');
    const parliamentarianList = document.getElementById('parliamentarian_id');

    if (!commissionSelect || !parliamentarianList) return;

    // Store all parliamentarians by commission
    let commissionParliamentarians = {};
    const baseUrl = window.location.href.split('/').slice(0, -2).join('/');
    fetch(`${baseUrl}/commissions/commissions-parliamentarians-json`)
        .then(response => response.json())
        .then(data => {
            commissionParliamentarians = data;
            // Initial update based on selected commission
            updateParliamentarians(commissionSelect.value);
        });

    // NOTE: The "chosen" library is a jQuery plugin. It hides the original
    // <select> element and creates a custom, styled dropdown. When we make a
    // selection, the plugin triggers a change event on the original, hidden
    // element using jQuery's internal event system. A vanilla JavaScript
    // attempt (addEventListener, event delegation) won't cut it here.
    $(commissionSelect).on('change', function() {
        updateParliamentarians(this.value);
    });

    function updateParliamentarians(commissionId) {
        parliamentarianList.innerHTML = '';
        if (!commissionId) return;

        const parliamentarians = commissionParliamentarians[commissionId] || [];
        parliamentarians.forEach(parliamentarian => {
            const li = document.createElement('li');
            const id = `parliamentarian_id-${parliamentarian.id}`;
            li.innerHTML = `
                <input type="checkbox" name="parliamentarian_id" value="${parliamentarian.id}" id="${id}">
                <label for="${id}">${parliamentarian.title}</label>
            `;
            parliamentarianList.appendChild(li);
        });
    }
});
