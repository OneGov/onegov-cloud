document.addEventListener('DOMContentLoaded', () => {
    const link = document.querySelector('[data-local-login-toggle]');
    const login = document.getElementById('local-login');

    if (!link || !login) {
        return;
    }

    if (!login.querySelector('.error')) {
        login.hidden = true;
        link.setAttribute('aria-expanded', 'false');
    }

    link.addEventListener('click', (event) => {
        event.preventDefault();
        login.hidden = !login.hidden;
        link.setAttribute('aria-expanded', String(!login.hidden));
    });
});
