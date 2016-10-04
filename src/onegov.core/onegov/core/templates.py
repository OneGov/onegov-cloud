""" Integrates the Chameleon template language.

This is basically a copy of more.chameleon, with the additional inclusion of a
gettext translation function defined by :mod:`onegov.core.i18n`.

To use a chameleon template, applications have to specify the templates
directiory, in addition to inheriting from
:class:`onegov.core.framework.Framework`.

For example::

    from onegov.core.framework import Framework

    class App(Framework):
        pass

    @App.template_directory()
    def get_template_directory():
        return 'templates'

    @App.path()
    class Root(object):
        pass

    @App.html(model=Root, template='index.pt')
    def view_root(self, request):
        return {
            'title': 'The Title'
        }

The folder can either be a directory relative to the app class or an absolute
path.

"""

import os.path

from cached_property import cached_property
from chameleon import PageTemplateLoader, PageTemplateFile
from chameleon.tal import RepeatDict
from chameleon.utils import Scope, decode_string
from onegov.core.framework import Framework


def get_default_vars(request, content):

    default = {
        'request': request,
        'translate': request.get_translate(for_chameleon=True)
    }

    default.update(content)

    return request.app.config.templatevariables_registry.get_variables(
        request, default)


class TemplateLoader(PageTemplateLoader):
    """ Extends the default page template loader with the ability to
    lookup macros in various folders.

    """

    @cached_property
    def macros(self):
        return MacrosLookup(self.search_path)


class MacrosLookup(object):
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

    def __init__(self, search_paths, name='macros.pt'):
        paths = (os.path.join(base, name) for base in search_paths)
        paths = (path for path in paths if os.path.isfile(path))

        # map each macro name to a template
        self.lookup = {
            name: template
            for template in (
                PageTemplateFile(path, search_paths)
                for path in reversed(list(paths))
            )
            for name in template.macros.names
        }

    def __getitem__(self, name):
        # macro names in chameleon are normalized internally and we need
        # to do the same to get the correct name in any case:
        name = name.replace('-', '_')
        return self.lookup[name].macros[name]


@Framework.template_loader(extension='.pt')
def get_template_loader(template_directories, settings):
    """ Returns the Chameleon template loader for templates with the extension
    ``.pt``.

    """

    return TemplateLoader(
        template_directories,
        default_extension='.pt',
        prepend_relative_search_path=False,
        auto_reload=False,
    )


@Framework.template_render(extension='.pt')
def get_chameleon_render(loader, name, original_render):
    """ Returns the Chameleon template renderer for the required template.

    """
    template = loader.load(name, 'xml')

    def render(content, request):

        variables = get_default_vars(request, content)
        return original_render(template.render(**variables), request)

    return render


def render_template(template, request, content):
    """ Renders the given template. Use this if you need to get the rendered
    value directly. If oyu render a view, this is not needed!

    """

    registry = request.app.config.template_engine_registry
    template = registry._template_loaders['.pt'][template]

    variables = get_default_vars(request, content)

    return template.render(**variables)


def render_macro(macro, request, content):
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

    variables = get_default_vars(request, content)
    variables.setdefault('__translate', variables['translate'])
    variables.setdefault('__convert', variables['translate'])
    variables.setdefault('__decode', decode_string)
    variables['repeat'] = RepeatDict({})
    variables.update(content)

    stream = list()
    macro.include(stream, Scope(variables), {})

    return ''.join(stream)
