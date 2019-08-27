var KEYS = {
    ESC: 27,
    ENTER: 13
};

var editAltText = function(target) {
    var existingValue = target.text();
    var availableTargets = $('.alt-text');
    var currentPosition = _.indexOf(availableTargets, target[0]);
    var url = $(target).parent().data('note-update-url');
    var finalizing = false;

    var selectText = function() {
        var range = document.createRange();
        range.selectNodeContents(target[0]);

        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    };

    var undo = function() {
        target.text(existingValue);
    };

    var abort = function() {
        finalizing = true;
        undo();

        // during blur the element is lost because we jump to the search
        // button once we lose focus, this locks the screen into position
        currentPosition = $('body')[0].scrollTop;

        target.blur();

        setTimeout(function() {
            $('body')[0].scrollTop = currentPosition;
        }, 0);
    };

    var commit = function() {
        finalizing = true;

        $.ajax({method: 'POST', url: url, data: {'note': target.text(), 'keep-timestamp': 'true'},
            success: function() {
                target.blur();
                target.removeClass('alt-text-missing');
                target.addClass('alt-text-changed-success');

                setTimeout(function() {
                    target.removeClass('alt-text-changed-success');
                }, 1000);
            },
            error: function() {
                abort(true);
                target.addClass('alt-text-changed-error');

                setTimeout(function() {
                    target.removeClass('alt-text-changed-error');
                }, 1000);
            }
        });
    };

    var onKeyDown = function(e) {
        switch (e.keyCode) {
            case KEYS.ESC:
                e.preventDefault();
                abort();
                break;
            case KEYS.ENTER:
                e.preventDefault();
                commit();
                break;
            default:
                return;
        }
    };

    var onFocus = function() {
        selectText();
    };

    var onBlur = function() {
        target.prop('contenteditable', false);
        target.parent().unbind('keydown', onKeyDown);
        target.unbind('blur', onBlur);
        target.unbind('focus', onFocus);

        // user clicked away, undo
        if (!finalizing) {
            undo();
        }
    };

    target.bind('focus', onFocus);
    target.bind('blur', onBlur);
    target.prop('contenteditable', true);
    target.parent().bind('keydown', onKeyDown);
    target.focus();
};

jQuery.fn.editAltText = function() {
    $(this).click(function(e) {
        var target = $(e.target);

        if (!target.hasClass('alt-text')) {
            return;
        }

        e.preventDefault();
        editAltText(target);
    });
};

$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).find('.editable-alt').editAltText();
});

$(document).ready(function() {
    $('.editable-alt').editAltText();
});
