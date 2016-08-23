/*
    This module will scans the page for input elements with either one of the
    following classes:

    * .image-url
    * .file-url
    * .internal-url

    It will then show a small button next to the input element which will
    allow for selection if an image url, a file url or an internal url
    respecitively.

    It's possible to use all of these classes at the same time. In this case
    a popup is shown when clicking the button. The user may then select if
    he wants to use an image, a file or an internal url.
*/


/* also used in editor.js */
function handleUploadError(json) {
    /* eslint-disable no-undefined */
    show_confirmation(json.message, undefined, "Ok");
    /* eslint-enable no-undefined */
}

// takes the given input element and wraps it with a button
// see http://foundation.zurb.com/sites/docs/v/5.5.3/components/forms.html#pre-postfix-labels-amp-actions
//
// the result is a reference to the button
var setup_internal_link_select = function(input) {
    input = $(input);

    var types = get_types(input);
    var button = get_button_face(types);

    if (types.length === 0) {
        return;
    }

    input.wrap('<div class="small-11 columns"></div>');
    input.closest('.columns').wrap('<div class="row collapse input-with-button">');
    input.closest('.row').append(
        '<div class="small-1 columns"><a class="button secondary postfix">' + button + '</a></div>'
    );

    var row = input.closest('.row');
    for (var i=0; i<types.length; i++) {
        row.addClass(types[i]);
    }

    if (types.length == 1) {
        row.find('.button').click(function(e) {
            on_internal_link_button_click(input, types[0]);
            e.preventDefault();
            return false;
        });
    } else {
        row.find('.button').click(function(e) {
            var popup_content = $('<div class="popup" />');

            // XXX put translatable strings in a separate file
            if (types.indexOf('image-url') != -1) {
                popup_content.append($('<a class="image-url">Bild</a>'));
            }

            if (types.indexOf('file-url') != -1) {
                popup_content.append($('<a class="file-url">Datei</a>'));
            }

            if (types.indexOf('internal-url') != -1) {
                popup_content.append($('<a class="internal-url">Interner Link</a>'));
            }

            popup_content.popup({
                'autoopen': true,
                'horizontal': 'right',
                'offsetleft': 8,
                'tooltipanchor': row.find('.button'),
                'transition': null,
                'type': 'tooltip',
                'onopen': function() {
                    var popup = $(this);

                    // any link clicked will close the popup
                    popup.find('a').click(function() {
                        popup.popup('hide');
                    });

                    popup.find('a').click(function(e) {
                        var type = get_types($(this))[0];
                        on_internal_link_button_click(input, type);
                        e.preventDefault();
                    });
                },
                'detach': true
            });

            e.preventDefault();
            return false;
        });
    }
};

var get_types = function(input) {
    var types = [];

    if ($(input).hasClass('image-url')) {
        types.push('image-url');
    }
    if ($(input).hasClass('file-url')) {
        types.push('file-url');
    }
    if ($(input).hasClass('internal-url')) {
        types.push('internal-url');
    }

    return types;
};

var get_button_face = function(types) {
    if (types.length == 1) {
        if (types[0] == 'image-url') {
            return '<i class="fa fa-picture-o"></i>';
        }
        if (types[0] == 'file-url') {
            return '<i class="fa fa-paperclip"></i>';
        }
        if (types[0] == 'internal-url') {
            return '<i class="fa fa-link"></i>';
        }
    }

    return '…';
};

var on_internal_link_button_click = function(input, type) {
    var form = $(input).closest('form');

    var virtual = $('<textarea><p></p></textarea>').redactor({
        plugins: ['imagemanager', 'filemanager', 'definedlinks'],
        fileUpload: form.data('file-upload-url'),
        fileManagerJson: form.data('file-list-url'),
        imageUpload: form.data('image-upload-url'),
        imageManagerJson: form.data('image-list-url'),
        definedLinks: form.data('sitecollection-url'),
        lang: 'de',
        fileUploadErrorCallback: handleUploadError,
        imageUploadErrorCallback: handleUploadError
    });

    var redactor = virtual.data('redactor');

    redactor.insert.html = jQuery.proxy(function(html) {
        var input = $(this);

        input.val(
            $(html).attr('src') || $(html).attr('href')
        );
    }, input);

    redactor.$textarea.on('insertedLinkCallback.redactor',
        jQuery.proxy(function(args) {
            var input = $(this[0]);
            var redactor = this[1];

            input.val(
                $(redactor.modal.getModal()).find('input[type="url"]').val()
            );

        }, [input, redactor])
    );

    redactor.$textarea.on('modalOpenedCallback.redactor',
        function() {
            this.$modal.addClass('input-with-button');
        }
    );

    redactor.$textarea.on('modalClosedCallback.redactor',
        function() {
            this.core.destroy();
        }
    );

    // required for IE to work >
    redactor.selection.addRange = function() {};
    redactor.selection.getCurrent = function() {
        return $(virtual).find('p');
    };
    // <

    var mapping = {
        'image-url': 'image.show',
        'file-url': 'file.show',
        'internal-url': 'link.show'
    };

    $(virtual).redactor(mapping[type]);
};

jQuery.fn.internal_link_select = function() {
    return this.each(function() {
        setup_internal_link_select(this);
    });
};

$(document).ready(function() {
    $('.image-url, .file-url, .internal-url').internal_link_select();
});