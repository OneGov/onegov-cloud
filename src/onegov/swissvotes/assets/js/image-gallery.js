$('.image-container > img').each(function () {
    var modal = document.getElementById(this.id.replace('img', 'modal'));
    var modalImg = document.getElementById(this.id.replace('img', 'modal-img'));
    var close = document.getElementById(this.id.replace('img', 'close'));
    $(this).on('click', function () {
        modal.style.display = "block";
        modalImg.src = this.src;
    });
    $(close).on('click', function () {
        modal.style.display = "none";
    });
});

$('.image-gallery-toggle').click(function () {
    $('.image-gallery-' + $(this).data('suffix') + ' .additional').show();
    $(this).hide();
});
