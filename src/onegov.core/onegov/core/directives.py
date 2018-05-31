import os.path

from datetime import datetime
from dectate import Action, Query
from inspect import isclass
from morepath.directive import HtmlAction
from onegov.core.utils import Bunch
from sedate import to_timezone, replace_timezone


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
    def __init__(self, model, form, render=None, template=None, load=None,
                 permission=None, internal=False, **predicates):
        self.form = form
        super().__init__(model, render, template, load, permission, internal,
                         **predicates)

    def perform(self, obj, *args, **kwargs):
        obj = wrap_with_generic_form_handler(obj, self.form)

        # if a request method is given explicitly, we honor it
        if 'request_method' in self.predicates:
            return super().perform(obj, *args, **kwargs)

        # otherwise we register ourselves twice, once for each method
        predicates = self.predicates.copy()

        self.predicates['request_method'] = 'GET'
        super().perform(obj, *args, **kwargs)

        self.predicates['request_method'] = 'POST'
        super().perform(obj, *args, **kwargs)

        self.predicates = predicates


def fetch_form_class(form_class, model, request):
    """ Given the form_class defined with the form action, together with
    model and request, this function returns the actual class to be used.

    """

    if isclass(form_class):
        return form_class
    else:
        return form_class(model, request)


def query_form_class(request, model, name=None):
    """ Queries the app configuration for the form class associated with
    the given model and name. Take this configuration for example::

        @App.form(model=Model, form_class=Form, name='foobar')
        ...

    The form class defined here can be retrieved as follows:

        query_form_class(request, model=Model, name='foobar')

    """

    appcls = request.app.__class__
    action = appcls.form.action_factory

    for a, fn in Query(action)(appcls):
        if not isinstance(a, action):
            continue

        if a.key_dict().get('name') == name:
            return fetch_form_class(a.form, model, request)


def wrap_with_generic_form_handler(obj, form_class):
    """ Wraps a view handler with generic form handling.

    This includes instantiatng the form with translations/csrf protection
    and setting the correct action.

    """

    def handle_form(self, request):

        _class = fetch_form_class(form_class, self, request)

        if _class:
            form = request.get_form(_class, model=self)
            form.action = request.url
        else:
            form = None

        return obj(self, request, form)

    return handle_form


class CronjobAction(Action):
    """ Register a cronjob. """

    config = {
        'cronjob_registry': Bunch
    }

    def __init__(self, hour, minute, timezone):
        self.hour = hour
        self.minute = minute
        self.timezone = timezone

    def identifier_by_hour_and_minute(self, hour, minute):
        return to_timezone(
            replace_timezone(
                datetime(2016, 1, 1, hour, minute),
                self.timezone
            ), 'UTC'
        )

    def identifier(self, **kw):
        # return a key to the hour/minute on a fixed day, this way it's
        # impossible to have two cronjobs running at the exact same time.
        hour = 0 if self.hour == '*' else self.hour
        return self.identifier_by_hour_and_minute(hour, self.minute)

    def discriminators(self, **kw):
        if self.hour != '*':
            return ()

        return tuple(
            self.identifier_by_hour_and_minute(hour, self.minute)
            for hour in range(0, 24) if hour != 0  # already in identifier
        )

    def perform(self, func, cronjob_registry):
        from onegov.core.cronjobs import register_cronjob

        register_cronjob(
            cronjob_registry, func, self.hour, self.minute, self.timezone)


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
