if ($('#current').length) {
    const positionCurrent = $('#current').position().top - $('.agenda-item-list').position().top;
    const listHeight = $('.agenda-item-list').height();
    const currentHeight = $('#current').height();

    $('.agenda-item-list').animate({
    scrollTop: positionCurrent - listHeight/2 + currentHeight/2
    })
}

$('.video-link a').on('click', function() {
    const timestamp = $(this).data('timestamp');
    const iframe = document.querySelector('#assembly-video-iframe iframe');
    var new_url = iframe.src.replace(/start=\d+/, `start=${timestamp}`);
    new_url = new_url + '&autoplay=1&allow=autoplay&mute=0';
    iframe.src = new_url;
});
