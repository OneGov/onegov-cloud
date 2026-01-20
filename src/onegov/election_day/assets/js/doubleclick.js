// Prevent users from submitting forms twice by double-clicking
// https://www.bram.us/2020/11/04/preventing-double-form-submissions/
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
        // Prevent if already submitting
        if (form.classList.contains('is-submitting')) {
            e.preventDefault();
        }

        // Add class to hook our visual indicator on
        form.classList.add('is-submitting');
        form.querySelector('input[type="submit"]').disabled = true;
    });
});
