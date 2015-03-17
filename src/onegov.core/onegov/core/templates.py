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

import chameleon

from onegov.core import Framework


@Framework.template_loader(extension='.pt')
def get_template_loader(template_directories, settings):
    """ Returns the Chameleon template loader for templates with the extension
    ``.pt``.

    """

    return chameleon.PageTemplateLoader(
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

        variables = {
            'request': request,
            'translate': request.get_translate(for_chameleon=True)
        }

        variables.update(content)
        return original_render(template.render(**variables), request)

    return render
