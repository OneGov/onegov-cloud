/*
    This module handles the dependent fields forms. Those are fields annotated
    by 'data-depends-on' attributes which contain the id of the input field
    and the value it is expected to have for the field with the attribute
    to be shown.

    Say you have a choice like this::

        <input name="delivery" type="radio" value="Pickup">
        <input name="delivery" type="radio" value="Fedex">

    And you want the user to fill out an address, if "Fedex" was chosen::

        <input name="address" type="text">

    You can annotate the address input field like this and it will only be
    shown if "Fedex" was chosen::

        <input name="address" data-depends-on="delivery/Fedex" type="text">

    Currently only works with radio buttons and checkboxes. By default, the
    closest label found is hidden as well (going upwards in the DOM).

    If this is not desired, use ``data-hide-label="false"``.
*/

/*
    Returns the choice value of the given field (string) in the given
    form (jquery object).
*/
var get_choices = function(form, field_name) {
    var fields = form.find('input[name="' + field_name + '"]:checked');
    if (fields.length === 0) return null;

    return _.map($(fields), function(f) { return $(f).val(); });
};


/*
    Returns the forms that contain at least one field with data-depends-on set.
*/
var get_relevant_forms = function() {
    return $('form:has(*[data-depends-on])');
};


/*
    Takes a data-depends-on value and returns the name of the field and the
    expected value of it.
*/
var get_dependency = function(input) {
    var data = input.data('depends-on');

    var name = data.split('/')[0];
    var value = data.substring(name.length + 1);

    var hide_label = true;

    if (! _.isUndefined(input.data('hide-label'))) {
        hide_label = input.data('hide-label');
    }

    return {'name': name, 'value': value, 'hide_label': hide_label};
};

/*
    Returns the target of the dependency
*/

var get_dependency_target = function(form, dependency) {
    return form.find('input[name="' + dependency.name + '"]');
};

/*
    Hookup the given form.
*/
var setup_depends_on = function(form) {
    var inputs = form.find('*[data-depends-on]');

    _.each(_.map(inputs, $), function(input) {
        var dependency = get_dependency(input);
        evaluate_dependency(form, input, dependency);

        get_dependency_target(form, dependency).on('click', function() {
            evaluate_dependency(form, input, dependency);
        });
    });
};

/*
    Evaluates the dependency and acts on the result.
*/
var evaluate_dependency = function(form, input, dependency) {
    if (_.contains(get_choices(form, dependency.name), dependency.value)) {
        input.show();
        input.closest('label').show().siblings('.error').show();
    } else {
        input.hide();
        if (dependency.hide_label) {
            input.closest('label').hide().siblings('.error').hide();
        }
    }
};

/*
    Setup the fields if there's a form
*/
$(document).ready(function() {
    if ($('form').length === 0) return;

    _.each(get_relevant_forms(), function(form) {
        setup_depends_on($(form));
    });
});
