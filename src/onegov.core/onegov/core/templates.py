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

from cached_property import cached_property
from onegov.core import Framework
from onegov.core import i18n


class I18nChameleonHelper(object):
    """ Bound to i18n.settings, this helper offers an easy way to access the
    translate method required for Chameleon using the request.

    The idea is to initialize this helper once per process and then feed it
    requests (see :meth:`get_translate`).
    """
    def __init__(self, settings):
        self.settings = settings

    def get_translate(self, request):
        """ Returns the translate method to the given request, or None
        if no such method is availabe.

        """
        if not self.languages:
            return None

        locale = self.settings.locale_negotiator(self.languages, request)
        locale = locale or self.settings.i18n.default_locale

        return self.translators.get(locale)

    @cached_property
    def translators(self):
        """ Returns all available translators. """
        return i18n.get_chameleon_translators(
            self.settings.domain,
            self.settings.localedir
        )

    @cached_property
    def languages(self):
        """ Returns all available languages in a set. """
        return set(self.translators.keys())


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

    If i18n settings are provided, the renderer will be set up with a
    translate function as defined in :mod:`onegov.core.i18n`.

    The reason for this happening here is the following Morepath issue:

    `<https://github.com/morepath/morepath/issues/298>`_
    """
    template = loader.load(name, 'xml')

    def render(content, request):

        # this is the part that should be done in get_template_loader,
        # once the morepath issue is fixed
        if not hasattr(loader, 'i18n_helper'):
            loader.i18n_helper = I18nChameleonHelper(
                request.app.registry.settings.i18n)
        # end

        variables = {
            'request': request,
            'translate': loader.i18n_helper.get_translate(request)
        }

        variables.update(content)
        return original_render(template.render(**variables), request)

    return render
