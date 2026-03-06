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
    var fields = form.find(
        'input[name="' + field_name + '"]:checked, ' +
        'select[name="' + field_name + '"], ' +
        'input[type="text"][name="' + field_name + '"]'
    );
    if (fields.length === 0) {
        return null;
    }

    return _.map($(fields), function(f) {
        return $(f).val();
    });
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
    return form.find(
        'input[name="' + dependency.name + '"], ' +
        'select[name="' + dependency.name + '"]'
    );
};

/*
    Evaluates the dependency and acts on the result.
*/
var evaluate_dependencies = function(form, input, dependencies, _handle_fieldset) {
    var visible = true;
    var hide_label = true;
    var handle_fieldset = _handle_fieldset || false;

    _.each(dependencies, function(dependency) {
        visible &= (dependency.invert ^ _.contains(get_choices(form, dependency.name), dependency.value));
        hide_label &= dependency.hide_label;
    });

    var fieldset = input.closest('fieldset');
    if (visible) {
        if (handle_fieldset) {
            fieldset.toggle(true);
        }
        var always_hidden = typeof input.attr('data-always-hidden') !== 'undefined';

        if (!always_hidden) {
            input.toggle(true);
        }

        input.closest('label, .group-label').show().siblings('.error').toggle(true);
        input.toggle(true);
    } else {
        input.toggle(false);
        if (hide_label) {
            input.closest('label, .group-label').hide().siblings('.error').toggle(false);
        }
        input.toggle(false);
        if (handle_fieldset && fieldset.find('input, select, textarea, label, .group-label').filter(':visible').length === 0) {
            fieldset.toggle(false);
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
        evaluate_dependencies(form, input, dependencies, false);

        _.each(dependencies, function(dependency) {
            var target = get_dependency_target(form, dependency);
            var trigger = 'change';
            if (target.is('[type="text"]')) {
                trigger = 'keyup';
            }
            target.on(trigger, function() {
                evaluate_dependencies(form, input, dependencies, true);
            });
        });
    });

    form.toggle(true);

    // since we were hiding our form during setup, the fieldset logic
    // doesn't work properly, so we need to handle them manually after
    // we unhide the form and already processed the fields
    var fieldsets = form.find('fieldset');

    _.each(_.map(fieldsets, $), function(fieldset) {
        if (fieldset.find('input, select, textarea, label, .group-label').filter(':visible').length === 0) {
            fieldset.toggle(false);
        }
    });
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
