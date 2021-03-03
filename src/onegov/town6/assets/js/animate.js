// adjust header based on manager global tools opened or not
$('#nav-bar').on('sticky.zf.unstuckfrom:top', function() {
    // console.log('on upscroll and show')
    var el = $(this).children(':first-child');
    var nav = $(this).find('.navigation');
    var img = $(this).find('img')
    var globals = $('.globals')
    if (el.data('modified')) {
        el.toggleClass('expanded')
        nav.toggleClass('expanded')
        img.toggleClass('scaled')
        globals.toggleClass('hide')
        el.data('modified', false)
    }
});


$('#nav-bar').on('sticky.zf.stuckto:top', function() {
    // console.log('on downscroll and hide')
    var el = $(this).children(':first-child');
    var nav = $(this).find('.navigation');
    var img = $(this).find('img')
    var globals = $('.globals')
    el.toggleClass('expanded')
    nav.toggleClass('expanded')
    img.toggleClass('scaled')
    globals.toggleClass('hide')
    el.data('modified', true)
});

$('#offCanvas').on('opened.zf.offCanvas', function (e) {
    $(this).find('#search').focus()
}).on('close.zf.offCanvas', function (e) {
    $(this).find('#search').blur()
})

$(document).on("keypress", function(e) {
    var code = e.keyCode || e.which
    // Ctrl+Shift+F or Ctrl+Shift+S
    if(e.ctrlKey && e.shiftKey && (code === 6 || code === 19) ) {
        $('#offCanvas').foundation('toggle', e)
    }
});
