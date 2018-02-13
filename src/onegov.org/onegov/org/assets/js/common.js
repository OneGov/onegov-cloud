// intercooler has the abilty to redirect depending on response headers
// we'd like for it to do the same with our own 'redirect-after' attribute
var setupRedirectAfter = function(elements) {
    elements.on('success.ic', function(_event, el) {
        var redirect_after = $(el).attr('redirect-after');
        if (!_.isUndefined(redirect_after)) {
            window.location = redirect_after;
        }

        return true;
    });
};

setupRedirectAfter($('a'));

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

// Toggle the selected state in image selection views when clicking the checkbox
$('.image-select input[type="checkbox"]').on('click', function(e) {
    var target = $(e.target);
    var checked = target.is(':checked');

    target.closest('.image-box').toggleClass('selected', checked);
});

// A generic error messages handler
function showAlertMessage(message, type, target) {
    type = type || 'alert';
    target = target || '#alert-boxes';

    var alert = $('<div />')
        .attr('data-alert', '')
        .attr('class', 'alert-box ' + (type || 'alert'))
        .text(message)
        .append($('<a href="#" class="close">&times;</a>'));

    $(target || '#alert-boxes').append(alert);
    $(document).foundation();
}

$(document).on('show-alert', function(_, data) {
    showAlertMessage(data.message, data.type, data.target);
});

$('[data-toggle]').toggleButton();

// handle intercooler errors generically
$(document).ajaxError(function(_e, xhr, _settings, error) {
    if (xhr.status === 502) {
        showAlertMessage(locale(
            "The server could not be reached. Please try again."
        ));
    } else if (xhr.status === 503) {
        showAlertMessage(locale(
            "This site is currently undergoing scheduled maintenance, " +
            "please try again later."
        ));
    } else if (xhr.status === 500) {
        showAlertMessage(locale(
            "The server responded with an error. We have been informed " +
            "and will investigate the problem."
        ));
    } else if (500 <= xhr.status && xhr.status <= 599) {
        // a generic error messages is better than nothing
        showAlertMessage(error || xhr.statusText);
    }
});

// show the slider once everything has loaded
$(document).ready(function() {
    $('.slider').css('opacity', 1);
});

// support some extraordinary styling
$(document).ready(function() {
    $('.requires-children').each(function() {
        var el = $(this);

        if ($(el.data('required-unless')).length === 0) {
            var children = el.find(el.data('required-children'));
            var required = parseInt(el.data('required-count'), 10);

            if (children.length < required) {
                el.hide();
            }
        }
    });
});

// send clicks from certain blocks down to the first link
$(document).ready(function() {
    $('.click-through').click(function() {
        window.location = $(this).find('a:first').attr('href');
    });
});

// automatically setup redirect after / confirmation dialogs for
// things loaded by intercooler
Intercooler.ready(function(element) {
    var el = $(element);

    // the ready event is fired on the body as well -> no action required there
    if (el.is('body')) {
        return;
    }

    $(el).find('a.confirm').confirmation();
    setupRedirectAfter(el);
});
