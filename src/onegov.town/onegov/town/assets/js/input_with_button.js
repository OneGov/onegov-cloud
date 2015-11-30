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
var wrap_input_with_button = function(el) {
    el = $(el);
    el.wrap('<div class="small-10 columns"></div>');
    el.closest('.columns').wrap('<div class="row collapse">');
    el.closest('.row').append(
        '<div class="small-2 columns"><a href="#" class="button postfix">…</div>'
    );

    return el.closest('.row').find('a.button');
};

var setup_internal_link_select = function(el) {
    var button = wrap_input_with_button(el);
    button.on('click', function() {
        on_internal_link_button_click(el);
    });
};

var on_internal_link_button_click = function(input) {
    var form = $(input).closest('form');

    var virtual = $('<textarea><p></p></textarea>').redactor({
        buttons: ['image', 'file', 'link'],
        plugins: ['imagemanager', 'filemanager', 'definedlinks'],
        fileUpload: form.data('file-upload-url'),
        fileManagerJson: form.data('file-list-url'),
        imageUpload: form.data('image-upload-url'),
        imageManagerJson: form.data('image-list-url'),
        definedLinks: form.data('sitecollection-url')
    });

    var redactor = virtual.data('redactor');

    redactor.insert.html = jQuery.proxy(function(html) {
        $(this).val($(html).attr('src') || $(html).attr('href'));
    }, input);

    var $input = $(input);

    if ($input.hasClass('image-url')) {
        redactor.$toolbar.find('.re-image').click();
    }

    else if ($input.hasClass('file-url')) {
        redactor.$toolbar.find('.re-file').click();
    }

    else if ($input.hasClass('internal-url')) {
        // does not work yet
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