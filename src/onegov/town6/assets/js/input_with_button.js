/*
    Adds a resource picker button to inputs marked with one or more of:

    * .image-url
    * .file-url
    * .internal-url
    * .photoalbum-url (programmatic picker only)

    The picker talks directly to the JSON endpoints exposed on the enclosing
    form. Keeping this independent of the rich-text editor also makes these
    fields usable on pages where no editor is loaded.
*/

/* also used in editor.js */
function handleUploadError(json) {
    /* eslint-disable no-undefined */
    show_confirmation(json.message, undefined, "Ok");
    /* eslint-enable no-undefined */
}

(function($) {
    'use strict';

    var active_picker = null;
    var picker_sequence = 0;

    var translate = function(text) {
        if (window.locale) {
            return window.locale(text);
        }
        return text;
    };

    var safe_url = function(value) {
        var compact;
        var scheme;

        value = String(value || '').trim();
        compact = value.replace(
            // Browsers ignore these characters while resolving a URL scheme.
            // eslint-disable-next-line no-control-regex
            /[\u0000-\u0020\u007f-\u00a0\u2028\u2029\ufeff]/g, ''
        );
        scheme = compact.match(/^([a-z][a-z0-9+.-]*):/i);
        if (!value || (scheme && ['http', 'https', 'mailto', 'tel'].indexOf(
            scheme[1].toLowerCase()
        ) === -1)) {
            return '';
        }
        return value;
    };

    var install_picker_styles = function() {
        if ($('#onegov-resource-picker-styles').length) {
            return;
        }

        $('<style id="onegov-resource-picker-styles">')
            .text(
                '.onegov-resource-picker-overlay {' +
                    'align-items:center;background:rgba(0,0,0,.55);' +
                    'display:flex;height:100%;justify-content:center;' +
                    'left:0;padding:1rem;position:fixed;top:0;width:100%;' +
                    'z-index:10050}' +
                '.onegov-resource-picker {' +
                    'background:#fff;box-shadow:0 1rem 3rem rgba(0,0,0,.3);' +
                    'max-height:90vh;max-width:48rem;overflow:auto;' +
                    'padding:1.25rem;width:100%}' +
                '.onegov-resource-picker-header {' +
                    'align-items:center;display:flex;gap:1rem;' +
                    'justify-content:space-between}' +
                '.onegov-resource-picker-header h2 {margin:0}' +
                '.onegov-resource-picker-close {' +
                    'background:transparent;border:0;cursor:pointer;' +
                    'font-size:2rem;line-height:1;padding:.25rem}' +
                '.onegov-resource-picker-kinds {' +
                    'display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}' +
                '.onegov-resource-picker-kinds button[aria-pressed="true"] {' +
                    'font-weight:bold;text-decoration:underline}' +
                '.onegov-resource-picker-status {margin:.75rem 0}' +
                '.onegov-resource-picker-search {margin:.75rem 0}' +
                '.onegov-resource-picker-list {' +
                    'max-height:50vh;overflow:auto}' +
                '.onegov-resource-picker-group {' +
                    'border:0;margin:.75rem 0;padding:0}' +
                '.onegov-resource-picker-group legend {' +
                    'font-weight:bold;margin-bottom:.35rem}' +
                '.onegov-resource-picker-images {' +
                    'display:flex;flex-wrap:wrap;gap:.5rem}' +
                '.onegov-resource-picker-choice {' +
                    'background:#fff;border:1px solid #bbb;cursor:pointer;' +
                    'display:block;margin:.25rem 0;padding:.5rem;' +
                    'text-align:left;width:100%}' +
                '.onegov-resource-picker-image {' +
                    'align-items:center;display:flex;height:10rem;' +
                    'justify-content:center;margin:0;width:10rem}' +
                '.onegov-resource-picker-image img {' +
                    'max-height:9rem;max-width:9rem}' +
                '.onegov-resource-picker-manual {' +
                    'align-items:flex-end;display:flex;gap:.5rem;' +
                    'margin:.75rem 0}' +
                '.onegov-resource-picker-manual label {flex:1}' +
                '.onegov-resource-picker-manual input {margin:0}' +
                '.onegov-resource-picker-upload {margin:.75rem 0}'
            )
            .appendTo('head');
    };

    var get_types = function(input) {
        var types = [];
        var field = $(input);

        if (field.hasClass('image-url')) {
            types.push('image-url');
        }
        if (field.hasClass('file-url')) {
            types.push('file-url');
        }
        if (field.hasClass('internal-url')) {
            types.push('internal-url');
        }

        return types;
    };

    var get_type_label = function(type) {
        if (type === 'image-url') {
            return translate('Image');
        }
        if (type === 'file-url') {
            return translate('File');
        }
        if (type === 'photoalbum-url') {
            return translate('Photo Album');
        }
        return translate('Internal Link');
    };

    var get_button_face = function(types) {
        if (types.length !== 1) {
            return '…';
        }
        if (types[0] === 'image-url') {
            return '<i class="fa fa-picture-o fas fa-image"></i>';
        }
        if (types[0] === 'file-url') {
            return '<i class="fa fas fa-paperclip"></i>';
        }
        return '<i class="fa fas fa-link"></i>';
    };

    var get_endpoint = function(form, type, operation) {
        if (type === 'image-url') {
            return form.data(
                operation === 'upload' ? 'image-upload-url' : 'image-list-url'
            );
        }
        if (type === 'file-url') {
            return form.data(
                operation === 'upload' ? 'file-upload-url' : 'file-list-url'
            );
        }
        if (type === 'photoalbum-url') {
            return form.data('photoalbum-list-url');
        }
        return form.data('sitecollection-url');
    };

    var abort_choice_requests = function(picker) {
        $.each(picker.choice_requests, function(_index, request) {
            request.abort();
        });
        picker.choice_requests = [];
    };

    var set_uploading = function(picker, uploading) {
        picker.uploading = uploading;
        picker.close.prop('disabled', uploading);
        picker.kinds.find('button').prop('disabled', uploading);
    };

    var close_picker = function() {
        if (!active_picker) {
            return true;
        }
        // A POST may already have reached the server and cannot be rolled
        // back reliably. Keep the picker open until it completes instead of
        // presenting a misleading cancel action that can orphan an upload.
        if (active_picker.uploading) {
            return false;
        }

        abort_choice_requests(active_picker);
        $(document).off('.onegov-resource-picker');
        active_picker.overlay.remove();
        $('body').css('overflow', active_picker.body_overflow);
        active_picker.button.trigger('focus');
        active_picker = null;
        return true;
    };

    var choose_value = function(input, value, label) {
        var on_select = active_picker && active_picker.on_select;

        try {
            if (on_select) {
                on_select(value, label || value);
            } else {
                input.val(value).trigger('change');
            }
        } finally {
            close_picker();
        }
    };

    var error_text = function(xhr) {
        var response = xhr && xhr.responseJSON;
        if (response && response.message) {
            return response.message;
        }
        return translate('The selection could not be loaded.');
    };

    var show_status = function(body, text, is_error) {
        var status = body.find('.onegov-resource-picker-status');
        status.text(text || '');
        status.attr('role', is_error ? 'alert' : 'status');
    };

    var add_search = function(body) {
        var search = $('<input type="search" class="onegov-resource-picker-search">');
        search.attr({
            'aria-label': translate('Select'),
            'placeholder': translate('Select') + '…'
        });
        search.on('input', function() {
            var query = String($(this).val()).toLocaleLowerCase();

            body.find('.onegov-resource-picker-choice').each(function() {
                var choice = $(this);
                choice.toggle(
                    String(choice.data('search')).toLocaleLowerCase()
                        .indexOf(query) !== -1
                );
            });
            body.find('.onegov-resource-picker-group').each(function() {
                var group = $(this);
                group.toggle(
                    group.find('.onegov-resource-picker-choice:visible').length > 0
                );
            });
        });
        body.find('.onegov-resource-picker-list').before(search);
    };

    var add_choice = function(container, label, value, image_url, input) {
        var choice = $('<button type="button" class="onegov-resource-picker-choice">');
        choice.data('search', label || value);
        choice.attr('aria-label', label || value);

        if (image_url) {
            choice.addClass('onegov-resource-picker-image');
            $('<img alt="" loading="lazy" decoding="async">')
                .attr('src', image_url)
                .appendTo(choice);
        } else {
            choice.text(label || value);
        }

        choice.on('click', function() {
            choose_value(input, value, label);
        });
        container.append(choice);
    };

    var render_images = function(body, data, input) {
        var list = body.find('.onegov-resource-picker-list').empty();

        $.each(data || [], function(_group_index, group_data) {
            var group = $('<fieldset class="onegov-resource-picker-group">');
            var images = $('<div class="onegov-resource-picker-images">');

            $('<legend>').text(group_data.group || '').appendTo(group);
            $.each(group_data.images || [], function(_image_index, image) {
                add_choice(
                    images,
                    image.title || image.image || translate('Image'),
                    image.image,
                    image.thumb,
                    input
                );
            });
            group.append(images).appendTo(list);
        });
        add_search(body);
    };

    var render_files = function(body, data, input) {
        var list = body.find('.onegov-resource-picker-list').empty();

        $.each(data || [], function(_file_index, file) {
            add_choice(list, file.title, file.link, null, input);
        });
        add_search(body);
    };

    var render_links = function(body, data, input) {
        var list = body.find('.onegov-resource-picker-list').empty();
        var groups = {};

        $.each(data || [], function(_link_index, link) {
            var group_name = link.group || '';
            var group = groups[group_name];

            if (!group) {
                group = $('<fieldset class="onegov-resource-picker-group">');
                $('<legend>').text(group_name).appendTo(group);
                groups[group_name] = group;
                list.append(group);
            }
            add_choice(group, link.name, link.url, null, input);
        });
        add_search(body);
    };

    var add_manual_link = function(body, input) {
        var manual = $('<form class="onegov-resource-picker-manual">');
        var label = $('<label>').text('URL');
        var url = $('<input type="text" inputmode="url">').val(input.val());
        var submit = $('<button type="submit" class="button">')
            .text(translate('Insert'));

        label.append(url);
        manual.append(label, submit);
        manual.on('submit', function(event) {
            var value = safe_url(url.val());

            event.preventDefault();
            if (!value) {
                show_status(
                    body, translate('Please enter a valid URL.'), true
                );
                url.trigger('focus');
                return;
            }
            choose_value(input, value, value);
        });
        body.append(manual);
    };

    var add_upload = function(body, form, type, input) {
        var upload_url = get_endpoint(form, type, 'upload');
        var upload = $('<div class="onegov-resource-picker-upload">');
        var label = $('<label>').text(translate('Upload'));
        var file_input = $('<input type="file" name="file">');

        if (!upload_url) {
            return;
        }
        if (type === 'image-url') {
            file_input.attr('accept', 'image/*');
        }

        label.append(file_input);
        upload.append(label);
        body.append(upload);

        file_input.on('change', function() {
            var file = this.files && this.files[0];
            var picker = active_picker;
            var cropper = window.OneGovBlockNote &&
                window.OneGovBlockNote.cropImageFile;

            var reset = function(message, is_error) {
                set_uploading(picker, false);
                file_input.prop('disabled', false).val('').trigger('focus');
                show_status(body, message || '', Boolean(is_error));
            };

            var upload_file = function(prepared_file) {
                var form_data = new FormData();

                form_data.append('file', prepared_file);
                show_status(body, translate('Upload') + '…', false);

                $.ajax({
                    'contentType': false,
                    'data': form_data,
                    'dataType': 'json',
                    'processData': false,
                    'type': 'POST',
                    'url': upload_url
                }).done(function(response) {
                    if (response.error || !response.filelink) {
                        reset(response.message || error_text(), true);
                        return;
                    }
                    set_uploading(picker, false);
                    choose_value(
                        input,
                        response.filelink,
                        response.filename || prepared_file.name
                    );
                }).fail(function(xhr, status) {
                    set_uploading(picker, false);
                    if (status === 'abort') {
                        return;
                    }
                    reset(error_text(xhr), true);
                });
            };

            if (!file) {
                return;
            }

            file_input.prop('disabled', true);
            set_uploading(picker, true);
            if (type !== 'image-url' || typeof cropper !== 'function') {
                upload_file(file);
                return;
            }

            show_status(body, translate('Crop image') + '…', false);
            Promise.resolve().then(function() {
                return cropper(file);
            }).then(function(cropped_file) {
                if (!cropped_file) {
                    reset('', false);
                    return;
                }
                upload_file(cropped_file);
            }).catch(function(error) {
                reset(
                    error && error.message ? error.message : error_text(),
                    true
                );
            });
        });
    };

    var load_choices = function(body, form, type, input) {
        var list_url = get_endpoint(form, type, 'list');
        var request;

        if (!list_url) {
            return;
        }

        show_status(body, '…', false);
        request = $.ajax({
            'cache': false,
            'dataType': 'json',
            'url': list_url
        }).done(function(data) {
            show_status(body, '', false);
            if (type === 'image-url') {
                render_images(body, data, input);
            } else if (type === 'file-url') {
                render_files(body, data, input);
            } else {
                render_links(body, data, input);
            }
        }).fail(function(xhr, status) {
            if (status === 'abort') {
                return;
            }
            show_status(body, error_text(xhr), true);
        });
        active_picker.choice_requests.push(request);
    };

    var render_type = function(type, input, form) {
        var picker = active_picker;
        var body = picker.body.empty();

        abort_choice_requests(picker);

        picker.title.text(get_type_label(type));
        picker.kinds.find('button').each(function() {
            var kind_button = $(this);
            kind_button.attr(
                'aria-pressed',
                String(kind_button.data('type') === type)
            );
        });

        $('<div class="onegov-resource-picker-status" aria-live="polite">')
            .appendTo(body);
        if (type === 'internal-url') {
            add_manual_link(body, input);
        } else if (type !== 'photoalbum-url') {
            add_upload(body, form, type, input);
        }
        $('<div class="onegov-resource-picker-list">').appendTo(body);
        load_choices(body, form, type, input);
    };

    /* eslint-disable-next-line complexity */
    var keep_focus_in_picker = function(event) {
        var focusable;
        var first;
        var last;

        if (event.key === 'Escape') {
            close_picker();
            return;
        }
        if (event.key !== 'Tab' || !active_picker) {
            return;
        }

        focusable = active_picker.panel.find(
            'a[href], button:not([disabled]), input:not([disabled]), ' +
            'select:not([disabled]), textarea:not([disabled]), [tabindex="0"]'
        ).filter(':visible');
        first = focusable.first()[0];
        last = focusable.last()[0];

        if (!active_picker.panel[0].contains(document.activeElement)) {
            event.preventDefault();
            $(event.shiftKey ? last : first).trigger('focus');
        } else if (
            event.shiftKey &&
            (document.activeElement === first ||
                document.activeElement === active_picker.panel[0])
        ) {
            event.preventDefault();
            $(last).trigger('focus');
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            $(first).trigger('focus');
        }
    };

    var open_picker = function(input, types, button, form, on_select) {
        var overlay;
        var panel;
        var header;
        var title;
        var close;
        var kinds;
        var body;
        var title_id;

        form = form || input.closest('form');
        if (!close_picker()) {
            return;
        }
        install_picker_styles();
        picker_sequence += 1;
        title_id = 'onegov-resource-picker-title-' + picker_sequence;

        overlay = $('<div class="onegov-resource-picker-overlay">');
        panel = $('<section class="onegov-resource-picker" role="dialog" aria-modal="true">');
        panel.attr({'aria-labelledby': title_id, 'tabindex': '-1'});
        header = $('<div class="onegov-resource-picker-header">');
        title = $('<h2>').attr('id', title_id);
        close = $('<button type="button" class="onegov-resource-picker-close">')
            .attr('aria-label', translate('Cancel'))
            .text('×');
        kinds = $('<div class="onegov-resource-picker-kinds" role="group">')
            .attr('aria-label', translate('Select'));
        body = $('<div class="onegov-resource-picker-body">');

        header.append(title, close);
        panel.append(header);
        if (types.length > 1) {
            $.each(types, function(_type_index, type) {
                var kind_button = $('<button type="button" class="button secondary">');
                kind_button.attr('aria-pressed', 'false');
                kind_button.data('type', type).text(get_type_label(type));
                kind_button.on('click', function() {
                    render_type(type, input, form);
                });
                kinds.append(kind_button);
            });
            panel.append(kinds);
        }
        panel.append(body);
        overlay.append(panel).appendTo('body');

        active_picker = {
            'body': body,
            'body_overflow': $('body')[0].style.overflow,
            'button': button,
            'choice_requests': [],
            'close': close,
            'kinds': kinds,
            'on_select': on_select,
            'overlay': overlay,
            'panel': panel,
            'title': title,
            'uploading': false
        };
        $('body').css('overflow', 'hidden');

        close.on('click', close_picker);
        overlay.on('mousedown', function(event) {
            if (event.target === overlay[0]) {
                close_picker();
            }
        });
        $(document).on('keydown.onegov-resource-picker', keep_focus_in_picker);

        render_type(types[0], input, form);
        close.trigger('focus');
    };

    var setup_internal_link_select = function(input) {
        var field = $(input);
        var types = get_types(field);
        var is_foundation_six;
        var input_columns;
        var button_columns;
        var row_classes;
        var row;
        var button;

        if (types.length === 0 || field.data('resource-picker-ready')) {
            return;
        }

        is_foundation_six = window.Foundation &&
            String(window.Foundation.version || '').indexOf('6.') === 0;
        input_columns = is_foundation_six ? 'small-11 cell' : 'small-11 columns';
        button_columns = is_foundation_six ? 'small-1 cell' : 'small-1 columns';
        row_classes = is_foundation_six ?
            'grid-x input-with-button' : 'row collapse input-with-button';

        field.data('resource-picker-ready', true);
        field.wrap($('<div>').addClass(input_columns));
        field.parent().wrap($('<div>').addClass(row_classes));
        row = field.closest('.input-with-button');
        button = $('<button type="button" class="button secondary postfix">')
            .attr('aria-label', types.map(get_type_label).join(', '))
            .html(get_button_face(types));
        $('<div>').addClass(button_columns).append(button).appendTo(row);

        $.each(types, function(_type_index, type) {
            row.addClass(type);
        });
        button.on('click', function() {
            open_picker(field, types, button, null, function(value) {
                field.val(value).trigger('input').trigger('change');
            });
        });
    };

    var normalize_type = function(type) {
        if (type === 'image' || type === 'image-url') {
            return 'image-url';
        }
        if (type === 'file' || type === 'file-url') {
            return 'file-url';
        }
        if (type === 'internal' || type === 'internal-url') {
            return 'internal-url';
        }
        if (type === 'photoalbum' || type === 'photoalbum-url') {
            return 'photoalbum-url';
        }
        throw new Error('Unknown OneGov URL picker type: ' + type);
    };

    // Programmatic entry point for editor tools and other custom controls:
    // onegovUrlPicker.open({form, type, value, returnFocus, onSelect})
    window.onegovUrlPicker = {
        'open': function(options) {
            var input = options.input ? $(options.input) : $('<input>');
            var form = $(options.form || input.closest('form'));
            var return_focus = $(options.returnFocus || document.activeElement);
            var type = normalize_type(options.type);

            input.val(options.value || input.val() || '');
            open_picker(
                input,
                [type],
                return_focus,
                form,
                options.onSelect
            );
        }
    };
    window.onegovResourcePicker = window.onegovUrlPicker;

    jQuery.fn.internal_link_select = function() {
        return this.each(function() {
            setup_internal_link_select(this);
        });
    };

    $(document).ready(function() {
        $('.image-url, .file-url, .internal-url').internal_link_select();
    });
})(jQuery);
