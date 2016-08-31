import os.path

from datetime import datetime
from dectate import Action
from inspect import isfunction
from morepath.directive import HtmlAction
from onegov.core.cronjobs import register_cronjob
from onegov.core.framework import Framework
from onegov.core.utils import Bunch
from sedate import to_timezone, replace_timezone


@Framework.directive('form')
class HtmlHandleFormAction(HtmlAction):
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
    def __init__(self, model, form, render=None, template=None,
                 permission=None, internal=False, **predicates):
        self.form = form
        super().__init__(model, render, template, permission, internal,
                         **predicates)

    def perform(self, obj, view_registry):

        keys = self.key_dict()

        wrapped = wrap_with_generic_form_handler(
            obj, self.form, keys.get('name'))

        if 'request_method' not in keys:

            keys['request_method'] = 'GET'
            view_registry.register_view(
                keys, wrapped,
                self.render, self.template,
                self.permission, self.internal)

            keys['request_method'] = 'POST'
            view_registry.register_view(
                keys, wrapped,
                self.render, self.template,
                self.permission, self.internal)
        else:
            view_registry.register_view(
                keys, wrapped,
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
class CronjobAction(Action):
    """ Register a cronjob. """

    config = {
        'cronjob_registry': Bunch
    }

    def __init__(self, hour, minute, timezone):
        self.hour = hour
        self.minute = minute
        self.timezone = timezone

    def identifier(self, cronjob_registry):
        # return a key to the hour/minute on a fixed day, this way it's
        # impossible to have two cronjobs running at the exact same time.
        return to_timezone(
            replace_timezone(
                datetime(2016, 1, 1, self.hour, self.minute),
                self.timezone
            ), 'UTC'
        )

    def perform(self, func, cronjob_registry):
        register_cronjob(
            cronjob_registry, func, self.hour, self.minute, self.timezone)


@Framework.directive('static_directory')
class StaticDirectoryAction(Action):
    """ Registers a static files directory. """

    config = {
        'staticdirectory_registry': Bunch
    }

    counter = iter(range(1, 123456789))

    def __init__(self):
        self.name = next(self.counter)

    def identifier(self, staticdirectory_registry):
        return self.name

    def perform(self, func, staticdirectory_registry):
        if not hasattr(staticdirectory_registry, 'paths'):
            staticdirectory_registry.paths = []

        path = func()

        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(self.code_info.path), path)

        staticdirectory_registry.paths.append(path)


class TemplateVariablesRegistry(object):

    __slots__ = ['callbacks']

    def __init__(self):
        self.callbacks = []

    def get_variables(self, request, base=None):
        base = base or {}

        for callback in self.callbacks:
            base.update(callback(request))

        return base


@Framework.directive('template_variables')
class TemplateVariablesAction(Action):
    """ Registers a set of global template variables for chameleon templates.

    Only exists once per application. Template variables with conflicting
    keys defined in child applications override the keys with the same
    name in the parent application. Non-conflicting keys are kept individually.

    Example::

        @App.template_variables()
        def get_template_variables(request):
            return {
                'foo': 'bar'
            }

    """

    config = {
        'templatevariables_registry': TemplateVariablesRegistry
    }

    counter = iter(range(1, 123456789))

    def __init__(self):
        # XXX I would expect this to work with a static name (and it does in
        # tests), but in real world usage the same name leads to overriden
        # paths
        self.name = next(self.counter)

    def identifier(self, templatevariables_registry):
        return self.name

    def perform(self, func, templatevariables_registry):
        templatevariables_registry.callbacks.append(func)
