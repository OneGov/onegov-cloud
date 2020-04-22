$('.image-container > img').each(function () {
    // console.log(this);
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
