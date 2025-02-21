""" Integrates the Chameleon template language.

This is basically a copy of more.chameleon, with the additional inclusion of a
gettext translation function defined by :mod:`onegov.core.i18n`.

To use a chameleon template, applications have to specify the templates
directory, in addition to inheriting from
:class:`onegov.core.framework.Framework`.

For example::

    from onegov.core.framework import Framework

    class App(Framework):
        pass

    @App.template_directory()
    def get_template_directory():
        return 'templates'

    @App.path()
    class Root:
        pass

    @App.html(model=Root, template='index.pt')
    def view_root(self, request):
        return {
            'title': 'The Title'
        }

The folder can either be a directory relative to the app class or an absolute
path.

"""
from __future__ import annotations

import os.path

from chameleon import PageTemplate as PageTemplateBase
from chameleon import PageTemplateFile as PageTemplateFileBase
from chameleon import PageTemplateLoader
from chameleon import PageTextTemplateFile
from chameleon.astutil import Builtin
from chameleon.tal import RepeatDict
from chameleon.utils import Scope
from functools import cached_property
from markupsafe import escape, Markup

from onegov.core.framework import Framework


from typing import Any, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from chameleon.zpt.template import Macro
    from collections.abc import Callable, Iterable, Mapping

    from .request import CoreRequest

_T = TypeVar('_T')


AUTO_RELOAD = os.environ.get('ONEGOV_DEVELOPMENT') == '1'

BOOLEAN_HTML_ATTRS = frozenset(
    [
        # List of Boolean attributes in HTML that should be rendered in
        # minimized form (e.g. <img ismap> rather than <img ismap="">)
        # From http://www.w3.org/TR/xhtml1/#guidelines (C.10)
        'compact',
        'nowrap',
        'ismap',
        'declare',
        'noshade',
        'checked',
        'disabled',
        'readonly',
        'multiple',
        'selected',
        'noresize',
        'defer',
    ]
)


class PageTemplate(PageTemplateBase):

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault('boolean_attributes', BOOLEAN_HTML_ATTRS)
        super().__init__(*args, **kwargs)


class PageTemplateFile(PageTemplateFileBase):

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault('boolean_attributes', BOOLEAN_HTML_ATTRS)
        super().__init__(*args, **kwargs)


def get_default_vars(
    request: CoreRequest,
    content: Mapping[str, Any],
    suppress_global_variables: bool = False
) -> dict[str, Any]:

    default = {
        'request': request,
        'translate': request.get_translate(for_chameleon=True),
        'escape': escape,
        'Markup': Markup
    }

    default.update(content)

    if suppress_global_variables:
        return default
    else:
        return request.app.config.templatevariables_registry.get_variables(
            request, default)


class TemplateLoader(PageTemplateLoader):
    """ Extends the default page template loader with the ability to
    lookup macros in various folders.

    """

    formats = {
        'xml': PageTemplateFile,
        'text': PageTextTemplateFile,
    }

    @cached_property
    def macros(self) -> MacrosLookup:
        return MacrosLookup(self.search_path, name='macros.pt')

    @cached_property
    def mail_macros(self) -> MacrosLookup:
        return MacrosLookup(self.search_path, name='mail_macros.pt')


class MacrosLookup:
    """ Takes a list of search paths and provides a lookup for macros.

    This means that when a macro is access through this lookup, it will travel
    up the search path of the template loader, to look for the macro and
    return with the first match.

    As a result, it is possible to have a macros.pt file in each search path
    and have them act as if they were one file, with macros further up the
    list of paths having precedence over the macros further down the path.

    For example, given the search paths 'foo' and 'bar', foo/macros.pt could
    define 'users' and 'page', while bar/macros.pt could define 'users' and
    'site'. In the lookup this would result in 'users' and 'page' being loaded
    loaded from foo and 'site' being loaded from bar.

    """

    def __init__(
        self,
        search_paths: Iterable[StrPath],
        name: str = 'macros.pt'
    ):
        paths = (os.path.join(base, name) for base in search_paths)
        paths = (path for path in paths if os.path.isfile(path))

        # map each macro name to a template
        self.lookup = {
            name: template
            for template in (
                PageTemplateFile(
                    path,
                    search_path=search_paths,
                    auto_reload=AUTO_RELOAD,
                )
                for path in reversed(list(paths))
            )
            for name in template.macros.names
        }

    def __getitem__(self, name: str) -> Macro:
        # macro names in chameleon are normalized internally and we need
        # to do the same to get the correct name in any case:
        name = name.replace('-', '_')
        return self.lookup[name].macros[name]


@Framework.template_loader(extension='.pt')
def get_template_loader(
    template_directories: list[str],
    settings: dict[str, Any]
) -> TemplateLoader:
    """ Returns the Chameleon template loader for templates with the extension
    ``.pt``.

    """

    return TemplateLoader(
        template_directories,
        default_extension='.pt',
        prepend_relative_search_path=False,
        auto_reload=AUTO_RELOAD,
    )


@Framework.template_render(extension='.pt')
def get_chameleon_render(
    loader: TemplateLoader,
    name: str,
    original_render: Callable[[str, CoreRequest], _T]
) -> Callable[[dict[str, Any], CoreRequest], _T]:
    """ Returns the Chameleon template renderer for the required template.

    """
    template = loader.load(name, 'xml')

    def render(content: dict[str, Any], request: CoreRequest) -> Any:

        variables = get_default_vars(request, content)
        return original_render(template.render(**variables), request)

    return render


def render_template(
    template: str,
    request: CoreRequest,
    content: dict[str, Any],
    suppress_global_variables: bool | Literal['infer'] = 'infer'
) -> Markup:
    """ Renders the given template. Use this if you need to get the rendered
    value directly. If oyu render a view, this is not needed!

    By default, mail templates (templates strting with 'mail_') skip the
    inclusion of global variables defined through the template_variables
    directive.

    """

    if suppress_global_variables == 'infer':
        suppress_global_variables = template.startswith('mail_')

    registry = request.app.config.template_engine_registry
    page_template = registry._template_loaders['.pt'][template]

    variables = get_default_vars(
        request, content, suppress_global_variables=suppress_global_variables)

    return Markup(page_template.render(**variables))  # nosec: B704


def render_macro(
    macro: Macro,
    request: CoreRequest,
    content: dict[str, Any],
    suppress_global_variables: bool = True
) -> Markup:
    """ Renders a :class:`chameleon.zpt.template.Macro` like this::

        layout.render_macro(layout.macros['my_macro'], **vars)

    This code is basically a stripped down version of this:
    `<https://github.com/malthe/chameleon/blob\
    /257c9192fea4b158215ecc4f84e1249d4b088753/src/chameleon\
    /zpt/template.py#L206>`_.

    As such it doesn't treat chameleon like a black box and it will probably
    fail one day in the future, if Chameleon is refactored. Our tests will
    detect that though.

    """

    if not hasattr(request, '_macro_variables'):
        variables = get_default_vars(
            request=request,
            content={},
            suppress_global_variables=suppress_global_variables
        )

        variables.setdefault('__translate', variables['translate'])
        variables.setdefault('__convert', variables['translate'])
        variables.setdefault('__decode', bytes.decode)
        variables.setdefault('__on_error_handler', Builtin('str'))
        variables.setdefault('target_language', None)
        request._macro_variables = variables  # type:ignore[attr-defined]
    else:
        variables = request._macro_variables.copy()

    variables.update(content)
    variables['repeat'] = RepeatDict({})

    stream: list[str] = []
    macro.include(stream, Scope(variables), {})

    return Markup(''.join(stream))  # nosec: B704
