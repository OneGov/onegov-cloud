""" Integrates the Chameleon template language.

This is basically a copy of more.chameleon, with the additional inclusion of a
gettext translation function defined by :mod:`onegov.core.i18n`.

To use a chameleon template, applications have to specify the templates
directiory, in addition to inheriting from
:class:`onegov.core.framework.Framework`.

For example::

    from onegov.core import Framework

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

from chameleon import PageTemplateLoader
from chameleon.tal import RepeatDict
from chameleon.utils import Scope, decode_string
from onegov.core import Framework


def get_default_vars(request):
    return {
        'request': request,
        'translate': request.get_translate(for_chameleon=True)
    }


@Framework.template_loader(extension='.pt')
def get_template_loader(template_directories, settings):
    """ Returns the Chameleon template loader for templates with the extension
    ``.pt``.

    """

    return PageTemplateLoader(
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

        variables = get_default_vars(request)
        variables.update(content)

        return original_render(template.render(**variables), request)

    return render


def render_template(template, request, content):
    """ Renders the given template. Use this if you need to get the rendered
    value directly. If oyu render a view, this is not needed!

    """

    template = request.app.registry._template_loaders['.pt'][template]

    variables = get_default_vars(request)
    variables.update(content)

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

    variables = get_default_vars(request)
    variables.setdefault('__translate', variables['translate'])
    variables.setdefault('__convert', variables['translate'])
    variables.setdefault('__decode', decode_string)
    variables['repeat'] = RepeatDict({})
    variables.update(content)

    stream = list()
    macro.include(stream, Scope(variables), {})

    return u''.join(stream)
