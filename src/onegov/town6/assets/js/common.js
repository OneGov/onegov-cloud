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

// sets up the given nodes with the functionality provided by common.js
// this is done at document.ready and can be repeated for out of band content
var processCommonNodes = function(elements, out_of_band) {
    var targets = $(elements);

    // intercooler redirects
    setupRedirectAfter(targets.find('a'));

    // Make sure files open in another window
    targets.find('.page-text a[href*="/datei/"]').attr('target', '_blank');

    // generic toggle button
    // targets.find('[data-toggle]').not('header *').toggleButton();

    // send an event to allow optional scripts to hook themselves up
    // (we only do out of band updates since it's not guaranteed that these
    // extra scripts are already set up with the event at the initial call)
    if (out_of_band !== false) {
        $(document).trigger('process-common-nodes', elements);
    }

    // send clicks from certain blocks down to the first link
    targets.find('.click-through').click(function() {
        var link = $(this).find('a:first');
        var handlers = $._data(link[0]);

        if (handlers && handlers.click && handlers.click.length > 0) {
            link[0].click();
        } else if (link.data('elementAdded.ic') === true) {
            Intercooler.triggerRequest(link);
        } else {
            window.location = link.attr('href');
        }

        return false;
    });
};

// setup common nodes
processCommonNodes($(document), false);

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

// Make sure files open in another window
$('.page-text a[href*="/datei/"]').attr('target', '_blank');

// Turn video links into clickable thumbnails
$('.page-text a.has-video').videoframe();

// Turn hashtags into links (happens in the backend at times, this should).
// This could be done in the templates (and it is done for the e-mail newsletter),
// but this way we can keep the code very simple.
var tagselectors = [
    '.has-hashtag',
    '.page-lead',
    '.news-lead',
    '.list-lead',
    '.occurrence-description',
    '.search-results > li',
    '.directory-fields .field-display dd',
    '.message .text'
];

// To avoid matching URLs, we need to make sure that the hashtag is not
// preceded by a letter, number or /. This is done by including the character
// before the hashtag. The character is then added back in the replacement.
var tagexpr = new RegExp('(^|[^a-zA-Z0-9/])(#[0-9a-zA-Zöäüéèà]{3,})', 'gi');

var highlightTags = function(target) {
    $(target).find(tagselectors.join(',')).each(function() {
        this.innerHTML = this.innerHTML.replace(tagexpr, function(fullMatch, beforeChar, hashtag) {
            // `beforeChar` captures the character before the hashtag
            // `hashtag` captures the hashtag itself

            return beforeChar + '<a class="hashtag" href="/search?q=' + encodeURIComponent(hashtag) + '">' + hashtag + '</a>';
        });
    });
};

highlightTags('#content');

$(document).on('process-common-nodes', function(_e, elements) {
    highlightTags(elements);
});

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

    target.closest('.image-container').toggleClass('selected', checked);
});

// A generic error messages handler
function showAlertMessage(message, type, target) {
    type = type || 'alert';
    target = target || '#alert-boxes';

    var alert = $('<div />')
        .attr('data-closable', '')
        .attr('class', 'alert-box callout ' + (type || 'alert'))
        .text(message);
    $(target || '#alert-boxes').append(alert);
}

$(document).on('show-alert', function(_, data) {
    showAlertMessage(data.message, data.type, data.target);
});

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
    } else if (xhr.status === 403) {
        showAlertMessage(locale(
            "Access denied. Please log in before continuing."
        ));
    } else if (500 <= xhr.status && xhr.status <= 599) {
        // a generic error messages is better than nothing
        showAlertMessage(error || xhr.statusText);
    }
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

// automatically setup redirect after / confirmation dialogs for
// things loaded by intercooler
Intercooler.ready(function(element) {
    var el = $(element);

    // the ready event is fired on the body as well -> no action required there
    if (el.is('body')) {
        return;
    }

    processCommonNodes(el, true);
});

// search reset buttons reset everything
$(document).ready(function() {
    $('.searchbox .reset-button').click(function(e) {
        var $inputs = $(this).closest('form').find('input');

        $inputs.val('');
        $inputs.filter(':visible:first').focus();

        e.preventDefault();
    });
});

function autoResize() {
    var newheight;
    var newwidth;
    var frame;

    for (frame of document.getElementsByClassName('resizeable')) {
        newheight = frame.contentWindow.document.body.scrollHeight;
        newwidth = frame.contentWindow.document.body.scrollWidth;
        frame.height = (newheight) + "px";
        frame.width = (newwidth) + "px";
    }

}

// Customize the sidebar. We need click events to browse to links with children
$(document).ready(function() {
    $('[data-click-target]').each(function() {
        var el = $(this);
        el.on('click', function() {
            var parent = el.parent();
            parent.off('click');
            window.location = el.data('click-target');
        });
    });
});

// qr code modals
function addModalImage(parent, rawData, fmt) {
    var src = 'data:image/' + fmt + ';base64,' + rawData;
    parent.append($(`<img class="qr" src="${src}">`));
}

function addModalDownload(parent, rawData, fmt) {
    var src = 'data:image/' + fmt + ';base64,' + rawData;
    var title = window.document.title;
    parent.append($(`<a class="button qr" download="qrcode_${title}.${fmt}" href="${src}">Download</a>`));
}

$('.qr-code-link').each(function() {
    var el = $(this);
    var imageParentID = el.data('image-parent');
    var imageParent = $(`#${imageParentID}`);
    var payload = el.data('payload') || window.location.href;
    var endpoint = el.data('endpoint');
    var fmt = 'png';

    el.on('click', function() {
        if (imageParent.find('img.qr').length) { return; }
        $.ajax({
            type: "GET",
            contentType: "image/" + fmt,
            url: `${endpoint}?encoding=base64&image_fmt=${fmt}&border=2&box_size=8&payload=${payload}`,
            statusCode: {
                200: function(resp) {
                    addModalImage(imageParent, resp, fmt);
                    addModalDownload(imageParent, resp, fmt);
                }
            }
        }).fail(function(_jqXHR) {
            // console.log(_jqXHR.statusMessage);
        });
    });
});

var page_refs = new ClipboardJS('.pageref');
page_refs.on('success', function(e) {
    // var success_msg = e.trigger.getAttribute('data-on-success');
    var msgContainer = $('#clipboard-copy');
    msgContainer.toggleClass('hidden');
    setTimeout(
        function() { msgContainer.toggleClass('hidden'); },
        1500
    );
    e.clearSelection();
});

// Allow custom reveal widths
$('.reveal[data-reveal-width]').on('open.zf.reveal', function() {
    this.style.width = this.dataset.revealWidth;
});

// Page edit form style adjustments
[...document.getElementsByClassName('indent-form-field')].forEach((formField) => {
    if (formField instanceof HTMLInputElement && formField.type === 'text') {
       formField.style.width = '90%';
    }
    let divWrapper = formField.parentElement.parentElement;
    divWrapper.style.marginLeft = '1.55rem';
});

// Height of header images
var w = window.matchMedia("(max-width: 700px)");
var header_height = $('#header').height();

if ($('.header-image .page-image').length) {
    var page_image = $('.header-image .page-image');
    if (w.matches) {
            var new_height = '60vw';
    } else {
            var new_height = 'calc(80vh - ' + header_height + 'px)';
    }
    page_image.css('padding-bottom', new_height);
}

$('a[data-back-link]').on('click', function(e) {
    if(document.referrer) {window.open(document.referrer,'_self');} else {history.go(-1);} return false;
});

$('.is-accordion-submenu-parent a span').on('click', function(e) {
    e.stopPropagation();
});
