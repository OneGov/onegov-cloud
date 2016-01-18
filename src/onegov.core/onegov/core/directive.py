from datetime import datetime
from inspect import isfunction
from morepath import generic
from morepath.directive import Directive, HtmlDirective, register_view
from onegov.core.cronjobs import register_cronjob
from onegov.core.framework import Framework
from sedate import to_timezone, replace_timezone


@Framework.directive('form')
class HtmlHandleFormDirective(HtmlDirective):
    """ Register Form view.

    Basically wraps the Morepath's ``html`` directive, registering both
    POST and GET (if no specific request method is given) and wrapping the
    view handler with :func:`wrap_with_generic_form_handler`.

    The form is either a class or a function. If it's a function, it is
    expected to return a form class when given an instance of the model.

    The form may also be None, which is useful under special circumstances.
    Generally you don't want that though.

    Example:

    .. code-block:: python

        @App.form(model=Root, template='form.pt',
                  permission=Public, form=LoginForm)
        def handle_form(self, request, form):
            if form.submitted():
                # do something if the form was submitted with valid data
            else:
                # do something if the form was not submitted or not
                # submitted correctly

            return {}  # template variables

    """
    def __init__(self, app, model, form, render=None, template=None,
                 permission=None, internal=False, **predicates):
        self.form = form
        super().__init__(app, model, render, template, permission, internal,
                         **predicates)

    def perform(self, registry, obj):
        registry.install_predicates(generic.view)
        registry.register_dispatch(generic.view)

        keys = self.key_dict()

        wrapped = wrap_with_generic_form_handler(
            obj, self.form, keys.get('name'))

        if 'request_method' not in keys:

            keys['request_method'] = 'GET'
            register_view(registry, keys, wrapped,
                          self.render, self.template,
                          self.permission, self.internal)

            keys['request_method'] = 'POST'
            register_view(registry, keys, wrapped,
                          self.render, self.template,
                          self.permission, self.internal)
        else:
            register_view(registry, keys, wrapped,
                          self.render, self.template,
                          self.permission, self.internal)


def wrap_with_generic_form_handler(obj, form_class, view_name):
    """ Wraps a view handler with generic form handling.

    This includes instantiatng the form with translations/csrf protection
    and setting the correct action.

    """

    def handle_form(self, request):

        if isfunction(form_class):
            _class = form_class(self, request)
        else:
            _class = form_class

        if _class:
            form = request.get_form(_class)
            form.action = request.link(self, name=view_name)
        else:
            form = None

        return obj(self, request, form)

    return handle_form


@Framework.directive('cronjob')
class CronjobDirective(Directive):
    """ Register a cronjob."""

    def __init__(self, app, hour, minute, timezone):
        super().__init__(app)

        self.hour = hour
        self.minute = minute
        self.timezone = timezone

    def identifier(self, registry):
        # return a key to the hour/minute on a fixed day, this way it's
        # impossible to have two cronjobs running at the exact same time.
        return to_timezone(
            replace_timezone(
                datetime(2016, 1, 1, self.hour, self.minute),
                self.timezone
            ), 'UTC'
        )

    def perform(self, registry, func):
        register_cronjob(registry, func, self.hour, self.minute, self.timezone)
