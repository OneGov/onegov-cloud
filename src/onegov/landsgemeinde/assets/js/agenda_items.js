if ($('#current').length) {
    if ($('#offCanvasSidebar').css('display') == 'none') {
        const positionCurrent = $('.sidebar #current').position().top - $('.sidebar .agenda-item-list').position().top;
        const listHeight = $('.sidebar .agenda-item-list').height();
        const currentHeight = $('.sidebar #current').height();

        $('.sidebar .agenda-item-list').animate({
            scrollTop: positionCurrent - listHeight/2 + currentHeight/2
        });
    } else {
        const positionCurrent = $('#offCanvasSidebar #current').position().top - $('#offCanvasSidebar .agenda-item-list').position().top;
        const listHeight = $('#offCanvasSidebar .agenda-item-list').height();
        const currentHeight = $('#offCanvasSidebar #current').height();

        $('.agenda-item-list').animate({
            scrollTop: positionCurrent - listHeight/2 + currentHeight/2
        });
    }
}

$('.video-link a').on('click', function() {
    const timestamp = $(this).data('timestamp');
    const iframe = document.querySelector('#assembly-video-iframe iframe');
    var new_url = iframe.src.replace(/start=\d+/, `start=${timestamp}`);
    new_url = new_url + '&autoplay=1&allow=autoplay&mute=0';
    iframe.src = new_url;
});
