document.addEventListener('DOMContentLoaded', () => {
    const link = document.querySelector('[data-local-login-toggle]');
    const login = document.getElementById('local-login');

    if (!link || !login) {
        return;
    }

    const setExpanded = (expanded) => {
        // foundation's grid display beats the hidden attribute
        login.style.display = expanded ? '' : 'none';
        link.setAttribute('aria-expanded', String(expanded));
    };

    if (!login.querySelector('.error')) {
        setExpanded(false);
    }

    link.addEventListener('click', (event) => {
        event.preventDefault();
        setExpanded(login.style.display === 'none');
    });
});
