var IconWidget = function(target) {
    var input = target.find('input');
    var icons = target.find('li');

    var activate = function(icon) {
        icons.toggleClass('active', false);
        icon.toggleClass('active', true);
    };

    icons.click(function() {
        var icon = $(this);
        input.val(icon.text());
        activate(icon);
    });

    activate(target.find(":contains('" + input.val() + "')"));
};

jQuery.fn.iconwidget = function() {
    return this.each(function() {
        IconWidget($(this));
    });
};

$(document).ready(function() {
    $('.icon-widget').iconwidget();
});
