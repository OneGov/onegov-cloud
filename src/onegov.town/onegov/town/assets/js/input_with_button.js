/*
    This module will scans the page for input elements with either one of the
    following classes:

    * .image-url
    * .file-url
    * .internal-url

    It will then show a small button next to the input element which will
    allow for selection if an image url, a file url or an internal url
    respecitively.
*/

// takes the given input element and wraps it with a button
// see http://foundation.zurb.com/sites/docs/v/5.5.3/components/forms.html#pre-postfix-labels-amp-actions
//
// the result is a reference to the button
var wrap_input_with_button = function(input) {
    input = $(input);

    input.wrap('<div class="small-11 columns"></div>');
    input.closest('.columns').wrap('<div class="row collapse input-with-button">');
    input.closest('.row').append(
        '<div class="small-1 columns"><a href="#" class="button postfix">…</div>'
    );

    var types = get_types(input);
    var row = input.closest('.row');

    for (var i=0; i<types.length; i++) {
        row.addClass(types[i]);
    }

    return input.closest('.row').find('a.button');
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

var setup_internal_link_select = function(el) {
    var button = wrap_input_with_button(el);
    button.on('click', function(e) {
        on_internal_link_button_click(el);
        e.preventDefault();
        return false;
    });
};

var on_internal_link_button_click = function(input) {
    var form = $(input).closest('form');

    var virtual = $('<textarea><p></p></textarea>').redactor({
        plugins: ['imagemanager', 'filemanager', 'definedlinks'],
        fileUpload: form.data('file-upload-url'),
        fileManagerJson: form.data('file-list-url'),
        imageUpload: form.data('image-upload-url'),
        imageManagerJson: form.data('image-list-url'),
        definedLinks: form.data('sitecollection-url'),
        lang: 'de'
    });

    var redactor = virtual.data('redactor');

    redactor.insert.html = jQuery.proxy(function(html) {
        var input = $(this[0]);
        var redactor = this[1];

        input.val(
            $(html).attr('src') || $(html).attr('href')
        );

        redactor.core.destroy();
    }, [input, redactor]);

    redactor.$textarea.on('insertedLinkCallback.redactor',
        jQuery.proxy(function(args) {
            var input = $(this[0]);
            var redactor = this[1];

            input.val(
                $(redactor.modal.getModal()).find('input[type="url"]').val()
            );

            redactor.core.destroy();
        }, [input, redactor])
    );

    redactor.$textarea.on('modalOpenedCallback.redactor',
        function() {
            this.$modal.addClass('input-with-button');
        }
    );

    var $input = $(input);

    if ($input.hasClass('image-url')) {
        $(virtual).redactor('image.show');
    }

    else if ($input.hasClass('file-url')) {
        $(virtual).redactor('file.show');
    }

    else if ($input.hasClass('internal-url')) {
        $(virtual).redactor('link.show');
    }

    else {
        throw "Unknown button type";
    }

};

jQuery.fn.internal_link_select = function() {
    return this.each(function() {
        setup_internal_link_select(this);
    });
};

$(document).ready(function() {
    $('.image-url, .file-url, .internal-url').internal_link_select();
});