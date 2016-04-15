// intercooler has the abilty to redirect depending on response headers
// we'd like for it to do the same with our own 'redirect-after' attribute
$('a').on('success.ic', function(_event, el) {
    var redirect_after = $(el).attr('redirect-after');
    if (!_.isUndefined(redirect_after)) {
        window.location = redirect_after;
    }

    return true;
});

// show the new content placeholder when hovering over the add content dropdown
$('.show-new-content-placeholder')
    .on('mouseenter', function() {
        var placeholder = $('<li>')
            .text($(this).text())
            .addClass('new-content-placeholder');

        $('.children').append(placeholder);
        placeholder.show();
    })
    .on('mouseleave', function() {
        $('.new-content-placeholder').remove();
    });

// initialize all foundation functions
$(document).foundation();

// get the footer height and write it to the footer_height setting if possible
$(document).find('#footer_height').val($('footer > div').height() + 'px');

// Add image captions
$('.page-text img[alt][alt!=""]').each(function() {
    var caption = $("<span>").text($(this).attr('alt'));
    $(this).after(caption);
});

// Make sure files open in another window
$('.page-text a[href*="/datei/"]').attr('target', '_blank');

// Turn video links into clickable thumbnails
$('.page-text a.has-video').videoframe();

// Disable scroll on elements which wish it disabled
$('.disable-scroll').on('mouseover', function() {
    var el = $(this);
    var height = el.height();
    var scrollHeight = el.get(0).scrollHeight;

    $(this).on('mousewheel', function(event) {
        var block = this.scrollTop === scrollHeight - height && event.deltaY < 0 || this.scrollTop === 0 && event.deltaY > 0;
        return !block;
    });
});

$('.disable-scroll').on('mouseout', function() {
    $(this).off('mousewheel');
});
