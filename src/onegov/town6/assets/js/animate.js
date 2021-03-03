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