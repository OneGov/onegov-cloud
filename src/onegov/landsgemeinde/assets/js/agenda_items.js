if ($('#current').length) {
    const positionCurrent = $('#current').position().top - $('.agenda-item-list').position().top;
    const listHeight = $('.agenda-item-list').height();
    const currentHeight = $('#current').height();

    $('.agenda-item-list').animate({
    scrollTop: positionCurrent - listHeight/2 + currentHeight/2
    })
}