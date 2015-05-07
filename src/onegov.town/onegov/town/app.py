""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from cached_property import cached_property
from contextlib import contextmanager
from onegov.core import Framework
from onegov.core import utils
from onegov.town.models import Town
from onegov.town.theme import TownTheme
from webassets import Bundle


class TownApp(Framework):
    """ The town application. Include this in your onegov.yml to serve it
    with onegov-server.

    """

    serve_static_files = True

    @property
    def town(self):
        """ Returns the cached version of the town. Since the town rarely
        ever changes, it makes sense to not hit the database for it every
        time.

        As a consequence, changes to the town object are not propagated,
        unless you use :meth:`update_town` or use the ORM directly.

        """
        return self.cache.get_or_create('town', self.load_town)

    def load_town(self):
        """ Loads the town from the SQL database. """
        return self.session().query(Town).first()

    @contextmanager
    def update_town(self):
        """ Yields the current town for an update. Use this instead of
        updating the town directly, because caching is involved. It's rather
        easy to otherwise update it wrongly.

        Example::
            with app.update_town() as town:
                town.name = 'New Name'

        """

        session = self.session()

        town = session.merge(self.town)
        yield town
        session.flush()

        self.cache.delete('town')

    @property
    def theme_options(self):
        return self.town.theme_options or {}

    @cached_property
    def webassets_path(self):
        return utils.module_path('onegov.town', 'assets')

    @cached_property
    def webassets_bundles(self):

        confirm = Bundle(
            'js/confirm.jsx',
            filters='jsx',
            output='bundles/confirm.bundle.js'
        )

        dropzone = Bundle(
            'js/dropzone.js',
            filters='jsmin',
            output='bundles/dropzone.bundle.js'
        )

        # do NOT minify the redactor, or the copyright notice goes away, which
        # is something we are not allowed to do per our license
        # ->
        redactor = Bundle(
            'js/redactor.min.js',
            output='bundles/redactor.bundle.js'
        )
        redactor_theme = Bundle(
            'css/redactor.css',
            output='bundles/redactor.bundle.css'
        )
        # <-

        editor = Bundle(
            'js/bufferbuttons.js',
            'js/imagemanager.js',
            'js/redactor.de.js',
            'js/editor.js',
            filters='jsmin',
            output='bundles/editor.bundle.js'
        )

        common = Bundle(
            'js/modernizr.js',
            'js/jquery.js',
            'js/fastclick.js',
            'js/foundation.js',
            'js/intercooler.js',
            'js/underscore.js',
            'js/react.js',
            'js/stickyfooter.js',
            confirm,
            'js/common.js',
            filters='jsmin',
            output='bundles/common.bundle.js'
        )

        return {
            'common': common,
            'dropzone': dropzone,
            'redactor': redactor,
            'redactor_theme': redactor_theme,
            'editor': editor
        }


@TownApp.template_directory()
def get_template_directory():
    return 'templates'


@TownApp.setting(section='core', name='theme')
def get_theme():
    return TownTheme()


@TownApp.setting(section='i18n', name='domain')
def get_i18n_domain():
    return 'onegov.town'


@TownApp.setting(section='i18n', name='localedir')
def get_i18n_localedir():
    return utils.module_path('onegov.town', 'locale')


@TownApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de'
