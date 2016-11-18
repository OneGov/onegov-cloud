/*
    Provides an easy way to toggle detail information with a button.

    Buttons which should toggle a content block need a data-toggle attribute,w
    which contains the selector of the content block which needs to be toggled.

    The initial state of the toggle is defined by the content block. If it
    is hidden (using style="display: none;"), the initial state is "untoggled",
    otherwise the state is "toggled".

    The state is stored as a class on the button.

    Using the style attribute as the initial style forces us to render the
    site correctly on the first pass, without having to change the visibility
    of elements through javascript leading to an expensive re-render.

    Additionally the toggled/untoggled class may be set on the button as well,
    though it will be corrected if it is wrong (so the ultimate source of
    truth is the style element of the target block).
*/

var isToggled = function(target) {
    return target.css('display') !== 'none' && true || false;
};

var ensureToggled = function(button, target, toggled) {
    button.toggleClass('toggled', toggled);

    if (target.is(':visible') !== toggled) {
        if (toggled) {
            target.show();
        } else {
            target.hide();
        }
    }
};

var clickToggled = function() {
    var button = $(this);
    var target = $(button.data('toggle'));

    ensureToggled(button, target, !isToggled(target));
};

var ToggleButton = function(button) {
    var target = $(button.data('toggle'));
    var toggled = isToggled(target);

    ensureToggled(button, target, toggled);
    button.click(clickToggled);
};

jQuery.fn.toggleButton = function() {
    return this.each(function() {
        ToggleButton($(this));
    });
};
