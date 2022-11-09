var error = document.querySelector('.error') != null;

if (error) {
    var errorfield = document.querySelector('.error input');
    var errorid = errorfield.getAttribute('id');
    errorid = errorid + '-error';

    errorfield.setAttribute('aria-describeby', errorid);
    errorfield.focus();
}