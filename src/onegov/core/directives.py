from __future__ import annotations

import os.path

from dectate import Action, Query, convert_dotted_name  # type:ignore[attr-defined]
from itertools import count

from morepath import render_json, Request
from morepath.directive import HtmlAction
from morepath.directive import isbaseclass
from morepath.directive import JsonAction
from morepath.directive import PredicateAction
from morepath.directive import PredicateFallbackAction
from morepath.directive import SettingAction
from morepath.settings import SettingRegistry, SettingSection

from onegov.core.utils import Bunch

from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath, StrPath
    from collections.abc import Callable, Mapping
    from webob import Response
    from wtforms import Form

    from .analytics import AnalyticsProvider
    from onegov.core import Framework
    from onegov.core.layout import Layout as CoreLayout
    from onegov.core.request import CoreRequest


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
    def __init__[RequestT: CoreRequest](
        self,
        model: type | str,
        form: type[Form] | Callable[[Any, RequestT], type[Form]],
        render: Callable[[Any, RequestT], Response] | str | None = None,
        template: StrOrBytesPath | None = None,
        load: Callable[[RequestT], Any] | str | None = None,
        permission: object | str | None = None,
        internal: bool = False,
        pass_model: bool = False,
        **predicates: Any
    ):
        self.form = form
        self.pass_model = pass_model
        super().__init__(model, render, template, load, permission, internal,
                         **predicates)

    def perform[RequestT: CoreRequest](
        self,
        obj: Callable[[Any, RequestT, Any], Any],
        *args: Any,
        **kwargs: Any
    ) -> None:

        wrapped = wrap_with_generic_form_handler(
            obj,
            self.form,
            pass_model=self.pass_model
        )

        # if a request method is given explicitly, we honor it
        if 'request_method' in self.predicates:
            return super().perform(wrapped, *args, **kwargs)

        # otherwise we register ourselves twice, once for each method
        predicates = self.predicates.copy()

        self.predicates['request_method'] = 'GET'
        super().perform(wrapped, *args, **kwargs)

        self.predicates['request_method'] = 'POST'
        super().perform(wrapped, *args, **kwargs)

        self.predicates = predicates


def fetch_form_class[FormT: Form, RequestT: CoreRequest](
    form_class: type[FormT] | Callable[[Any, RequestT], type[FormT]],
    model: object,
    request: RequestT
) -> type[FormT]:
    """ Given the form_class defined with the form action, together with
    model and request, this function returns the actual class to be used.

    """

    if isinstance(form_class, type):
        return form_class
    else:
        return form_class(model, request)


def query_form_class(
    request: CoreRequest,
    model: object,
    name: str | None = None
) -> type[Form] | None:
    """ Queries the app configuration for the form class associated with
    the given model and name. Take this configuration for example::

        @App.form(model=Model, form_class=Form, name='foobar')
        ...

    The form class defined here can be retrieved as follows:

        query_form_class(request, model=Model, name='foobar')

    """

    appcls = request.app.__class__
    action = appcls.form.action_factory
    assert issubclass(action, HtmlHandleFormAction)

    for a, fn in Query(action)(appcls):
        if not isinstance(a, action):
            continue

        if a.key_dict().get('name') == name:
            return fetch_form_class(
                a.form,  # type:ignore[arg-type]
                model,
                request
            )
    return None


def wrap_with_generic_form_handler[T, RequestT: CoreRequest, FormT: Form](
    obj: Callable[[T, RequestT, FormT], Any],
    form_class: type[FormT] | Callable[[T, RequestT], type[FormT]],
    pass_model: bool,
) -> Callable[[T, RequestT], Any]:
    """ Wraps a view handler with generic form handling.

    This includes instantiating the form with translations/csrf protection
    and setting the correct action.

    """

    def handle_form(self: T, request: RequestT) -> Any:

        _class = fetch_form_class(form_class, self, request)

        if _class:
            form = request.get_form(_class, model=self, pass_model=pass_model)
            form.action = request.url  # type: ignore[attr-defined]
        else:
            # FIXME: This seems potentially bad, do we actually ever want
            #        to handle a missing form within the view? If we don't
            #        we could just throw an exception here...
            form = None

        return obj(self, request, form)  # type:ignore[arg-type]

    return handle_form


class CronjobAction(Action):
    """ Register a cronjob. """

    config = {
        'cronjob_registry': Bunch
    }
    counter: ClassVar = count(1)

    def __init__(
        self,
        hour: int | str,
        minute: int | str,
        timezone: str,
        once: bool = False
    ):
        self.hour = hour
        self.minute = minute
        self.timezone = timezone
        self.name = next(self.counter)
        self.once = once

    def identifier(self, **kw: Any) -> int:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: Callable[[CoreRequest], Any],
        cronjob_registry: Bunch
    ) -> None:
        from onegov.core.cronjobs import register_cronjob

        register_cronjob(
            registry=cronjob_registry,
            function=func,
            hour=self.hour,
            minute=self.minute,
            timezone=self.timezone,
            once=self.once)


class AnalyticsProviderAction(Action):
    """ Register an analytics provider. """

    config = {
        'analytics_provider_registry': dict
    }

    def __init__(self, name: str, title: str) -> None:
        self.name = name
        self.title = title

    def identifier(  # type:ignore[override]
        self,
        analytics_provider_registry: dict[str, AnalyticsProvider]
    ) -> str:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: type[AnalyticsProvider],
        analytics_provider_registry: dict[str, type[AnalyticsProvider]]
    ) -> None:

        # NOTE: We assume that this decorator will be directly used
        #       at the class definition site, otherwise it would be
        #       unsafe to set attributes on the class
        func.name = self.name
        func.title = self.title

        analytics_provider_registry[self.name] = func


class StaticDirectoryAction(Action):
    """ Registers a static files directory. """

    config = {
        'staticdirectory_registry': Bunch
    }
    counter: ClassVar = count(1)

    def __init__(self) -> None:
        self.name = next(self.counter)

    def identifier(  # type:ignore[override]
        self,
        staticdirectory_registry: Bunch
    ) -> int:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: Callable[..., Any],
        staticdirectory_registry: Bunch
    ) -> None:

        if not hasattr(staticdirectory_registry, 'paths'):
            staticdirectory_registry.paths = []

        path = func()

        if not os.path.isabs(path):
            assert self.code_info is not None
            path = os.path.join(os.path.dirname(self.code_info.path), path)

        staticdirectory_registry.paths.append(path)


class TemplateVariablesRegistry:

    __slots__ = ('callbacks',)

    def __init__(self) -> None:
        self.callbacks: list[Callable[[CoreRequest], dict[str, Any]]] = []

    def get_variables(
        self,
        request: CoreRequest,
        base: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
    counter: ClassVar = count(1)

    def __init__(self) -> None:
        # XXX I would expect this to work with a static name (and it does in
        # tests), but in real world usage the same name leads to overriden
        # paths
        self.name = next(self.counter)

    def identifier(  # type:ignore[override]
        self,
        templatevariables_registry: TemplateVariablesRegistry
    ) -> int:
        return self.name

    def perform(  # type:ignore[override]
        self,
        func: Callable[[CoreRequest], dict[str, Any]],
        templatevariables_registry: TemplateVariablesRegistry
    ) -> None:
        templatevariables_registry.callbacks.append(func)


class ReplaceSettingSectionAction(Action):
    """ Register application setting in a section.

    In contrast to the regular SettingSectionAction this completely
    replaces the existing section.
    """

    config = {'setting_registry': SettingRegistry}

    depends = [SettingAction]

    def __init__(self, section: str) -> None:
        self.section = section

    def identifier(self, **kw: Any) -> str:
        return self.section

    def perform(  # type: ignore[override]
        self,
        obj: Callable[[], Mapping[str, Any]],
        setting_registry: SettingRegistry
    ) -> None:

        section = SettingSection()
        setattr(setting_registry, self.section, section)

        for setting, value in obj().items():
            setattr(section, setting, value)


class ReplaceSettingAction(SettingAction):
    """ A setting action that takes precedence over a replaced section.

    So we can override single settings without overriding the whole
    section.
    """

    depends = [ReplaceSettingSectionAction]


class Layout(Action):
    """
    Registers a layout for a model. This is used to show breadcrumbs
    for search results.
    """

    app_class_arg = True
    depends = [PredicateFallbackAction, PredicateAction]
    filter_convert = {'model': convert_dotted_name}
    filter_compare = {'model': isbaseclass}

    def __init__(self, model: type) -> None:
        self.model = model

    def identifier(  # type:ignore[override]
        self,
        app_class: type[Framework]
    ) -> str:
        return str(self.model)

    def perform(  # type:ignore[override]
        self,
        obj: type[CoreLayout],
        app_class: type[Framework]
    ) -> None:

        layout_class = obj
        # `lambda self, obj, request` is required to match the signature
        app_class.get_layout.register(  # type:ignore[attr-defined]
            lambda self, obj, request: layout_class(obj, request),
            model=self.model)


def render_json_open_data(content: object, request: Request) -> Response:
    """ Like :func:`morepath.render_json`, but adds an
    ``Access-Control-Allow-Origin: *`` header to GET and HEAD responses,
    making the endpoint accessible from browser scripts on any origin.
    """
    response = render_json(content, request)
    if request.method in ('GET', 'HEAD'):
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response


class ExtendedJsonAction(JsonAction):
    """ Extends the morepath json directive with an ``open_data`` parameter.

    When ``open_data=False`` (the default), the views should not be
    publicly accessible cross-origin.

    When ``open_data=True``, the view's GET and HEAD responses
    will include an ``Access-Control-Allow-Origin: *`` header, making it
    usable from browser scripts on any origin.
    """

    def __init__(
        self,
        model: type | str,
        render: Callable[[Any, Any], Response] | str | None = None,
        template: StrPath | None = None,
        load: Callable[[Any], Any] | str | None = None,
        permission: object = None,
        internal: bool = False,
        open_data: bool = False,
        **predicates: Any,
    ) -> None:
        if open_data and render is None:
            render = render_json_open_data
        super().__init__(
            model, render, template, load, permission, internal, **predicates
        )
