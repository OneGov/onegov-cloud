const errorfield = document.querySelector('.error input');

if (errorfield) {
    var errorid = errorfield.getAttribute('id');
    errorid = errorid + '-error';

    errorfield.setAttribute('aria-describeby', errorid);
    errorfield.focus();
}
