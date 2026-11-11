// shows a spinner while the AI translation is loading
$(document).on('click', '.translate-link', function() {
    $(this).addClass('in-progress');
});

// remove the spinner when the page is restored from the back/forward cache
$(window).on('pageshow', function() {
    $('.translate-link').removeClass('in-progress');
});
