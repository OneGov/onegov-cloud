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
    if (fields.length === 0) {
        return null;
    }

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
var get_dependencies = function(input) {
    var hide_label = true;
    if (!_.isUndefined(input.data('hide-label'))) {
        hide_label = input.data('hide-label');
    }

    var dependencies = input.data('depends-on').split(';');
    return _.map(dependencies, function(dependency) {
        var name = dependency.split('/')[0];
        var value = dependency.substring(name.length + 1);
        var invert = value.indexOf('!') === 0;
        if (invert) {
            value = value.substring(1);
        }

        return {'name': name, 'value': value, 'invert': invert, 'hide_label': hide_label};
    });
};

/*
    Returns the target of the dependency
*/

var get_dependency_target = function(form, dependency) {
    return form.find('input[name="' + dependency.name + '"]');
};

/*
    Evaluates the dependency and acts on the result.
*/
var evaluate_dependencies = function(form, input, dependencies) {
    var visible = true;
    var hide_label = true;

    _.each(dependencies, function(dependency) {
        visible &= (dependency.invert ^ _.contains(get_choices(form, dependency.name), dependency.value));
        hide_label &= dependency.hide_label;
    });

    if (visible) {
        input.show();
        input.closest('label, .group-label').show().siblings('.error').show();
    } else {
        input.hide();
        if (hide_label) {
            input.closest('label, .group-label').hide().siblings('.error').hide();
        }
    }
};

/*
    Hookup the given form.
*/
var setup_depends_on = function(form) {
    var inputs = form.find('*[data-depends-on]');

    // our dependency evaluation is *much* faster if we don't trigger any
    // rendering reflows -> at even a moderate number of items this can take
    // seconds if we don't hide the form
    form.hide();

    _.each(_.map(inputs, $), function(input) {
        var dependencies = get_dependencies(input);
        evaluate_dependencies(form, input, dependencies);

        _.each(dependencies, function(dependency) {
            get_dependency_target(form, dependency).on('click', function() {
                evaluate_dependencies(form, input, dependencies);
            });
        });
    });

    form.show();
};

/*
    Setup the fields if there's a form
*/
$(document).ready(function() {
    if ($('form').length === 0) {
        return;
    }

    _.each(get_relevant_forms(), function(form) {
        setup_depends_on($(form));
    });
});
