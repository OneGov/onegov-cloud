// adjust header based on manager global tools opened or not
$('#nav-bar').on('sticky.zf.unstuckfrom:top', function() {
    const header = document.getElementById('header')
    fireHeaderResized(header, false)

    var el = $(this).children(':first-child');
    var nav = $(this).find('.navigation');
    var img = $(this).find('img')
    var svg = $(this).find('svg')

    if (el.data('modified')) {
        el.toggleClass('shrink')
        nav.toggleClass('shrink')
        img.toggleClass('scaled')
        svg.toggleClass('scaled')
        el.data('modified', false)
    }
});

$('#nav-bar').on('sticky.zf.stuckto:top', function() {
    const header = document.getElementById('header')
    fireHeaderResized(header, true)

    var el = $(this).children(':first-child');
    var nav = $(this).find('.navigation');
    var img = $(this).find('img')
    var svg = $(this).find('svg')
    el.toggleClass('shrink')
    nav.toggleClass('shrink')
    img.toggleClass('scaled')
    svg.toggleClass('scaled')
    el.data('modified', true)
});

$('.side-navigation.drilldown').find('ul.current-list').removeClass( "invisible" );

if ($('#page-search').length) {
    $('.search-button').click(function(){
            $('#page-search').find('#search').focus()
        });
}

$('#offCanvasSearch').on('opened.zf.offCanvas', function (e) {
    $(this).find('#search').focus()
})

$(document).on("keypress", function(e) {
    var code = e.keyCode || e.which
    // Ctrl+Shift+F or Ctrl+Shift+S
    if(e.ctrlKey && e.shiftKey && (code === 6 || code === 19) ) {
        $('#offCanvas').foundation('toggle', e)
    }
});

$(".rotate").parent().click(function(){
    $(this).children('.fa').eq(0).toggleClass("down");
});

/**
 * Signal that the header was resized.
 *
 * If you use transitions when resizing the header, pass `true` so that the
 * event waits for the transition to be finished before firing. If you don't
 * wait for the transition, you might end up with old height information.
 */
function fireHeaderResized(element, withTransition) {

    function fireEvent() {
        const event = new CustomEvent('onegov.header-resized')
        element.dispatchEvent(event)
    }

    if (withTransition) {
        element.addEventListener("transitionend", fireEvent)
    } else {
        fireEvent()
    }
}