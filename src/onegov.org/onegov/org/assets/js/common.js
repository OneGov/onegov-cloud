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

    // intercooler integration (only done for dynamic content, and if
    // the nodes weren't already processed by intercooler)
    if (out_of_band !== false) {
        if (_.isUndefined(elements.data('ic-event-id'))) {
            Intercooler.processNodes(targets);
        }
    }

    // intercooler redirects
    setupRedirectAfter(targets.find('a'));

    // initialise zurb foundation (only works on the document level)
    $(document).foundation();

    // Make sure files open in another window
    targets.find('.page-text a[href*="/datei/"]').attr('target', '_blank');

    // generic toggle button
    targets.find('[data-toggle]').toggleButton();

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
$(document).ready(function() {
    processCommonNodes($(document), false);
})

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
var tagexpr = new RegExp('(#[0-9a-zA-Zöäüéèà]{3,})', 'gi');

var highlightTags = function(target) {
    $(target).find(tagselectors.join(',')).each(function() {
        this.innerHTML = this.innerHTML.replace(
            tagexpr, function(match) {
                return '<a class="hashtag" href="/search?q=' + encodeURIComponent(match) + '">' + match + '</a>';
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
