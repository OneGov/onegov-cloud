var TextModulePicker = function(target) {
    var input = target.parent().find('textarea');
    var label = target.find('.text-module-picker-label');
    var text_modules = target.find('.text-module-option');

    var toggle_dropdown = function(expanded) {
        target.toggleClass('active', expanded);
        label.attr('aria-expanded', expanded.toString());
        text_modules.parent().attr('aria-hidden', (!expanded).toString());
    }

    var pick = function(text_module) {
        var text = text_module.data('value');
        var cursor_pos = input.prop('selectionStart');
        var selection_end = input.prop('selectionEnd');
        var orig_text = input.val();
        input.val(orig_text.substring(0, cursor_pos) + text + orig_text.substring(selection_end));

        var new_cursor_pos = cursor_pos + text.length;
        input.focus();
        input.prop('selectionStart', new_cursor_pos);
        input.prop('selectionEnd', new_cursor_pos);
    };

    target.click(function(e) {
        e.stopPropagation();
        toggle_dropdown(true);
        return false;
    });

    $(document).click(function() {
        toggle_dropdown(false);
    });

    text_modules.click(function(e) {
        e.stopPropagation();
        var text_module = $(this);
        pick(text_module);
        toggle_dropdown(false);
        return false;
    });

    text_modules.keydown(function(e) {
        var text_module = $(this);
        if(e.which == 13 || e.keyCode == 13) {
            e.stopPropagation();
            e.preventDefault();
            pick(text_module);
            toggle_dropdown(false);
            return false;
        } else if(e.which == 38 || e.keyCode == 38) {
            e.stopPropagation();
            e.preventDefault();
            text_module.prev().focus();
            return false;
        } else if(e.which == 40 || e.keyCode == 40) {
            e.stopPropagation();
            e.preventDefault();
            text_module.next().focus();
            return false;
        }
    })

    input.keydown(function(e) {
        if(e.ctrlKey && (e.which == 73 || e.keyCode == 73)) {
            e.stopPropagation();
            e.preventDefault();
            toggle_dropdown(true);
            text_modules.eq(0).focus();
            return false;
        }
    });
};

jQuery.fn.textmodulepicker = function() {
    return this.each(function() {
        TextModulePicker($(this));
    });
};

$(document).ready(function() {
    $('.text-module-picker').textmodulepicker();
});