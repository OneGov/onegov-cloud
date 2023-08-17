var positionCurrent = $('#current').position().top - $('.agenda-item-list').position().top;
var listHeight = $('.agenda-item-list').height();
var currentHeight = $('#current').height();

$('.agenda-item-list').animate({
scrollTop: positionCurrent - listHeight/2 + currentHeight/2
})