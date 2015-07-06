""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

import transaction

from cached_property import cached_property
from contextlib import contextmanager
from onegov.core import Framework
from onegov.core import utils
from onegov.town import log
from onegov.town.initial_content import add_builtin_forms
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

    def configure_application(self, **cfg):
        super(TownApp, self).configure_application(**cfg)

        if self.has_database_connection:
            schema_prefix = self.namespace + '-'
            town_schemas = [
                s for s in self.session_manager.list_schemas()
                if s.startswith(schema_prefix)
            ]

            for schema in town_schemas:
                self.session_manager.set_current_schema(schema)

                session = self.session()
                add_builtin_forms(session)
                session.flush()
                transaction.commit()

            log.info('Updated all builtin forms')

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

        map_theme = Bundle(
            'css/leaflet.css',
            filters='cssmin',
            output='bundles/map_theme.bundle.css'
        )

        map = Bundle(
            'js/leaflet.js',
            'js/leaflet-google.js',
            'js/map.js',
            filters='jsmin',
            output='bundles/map.bundle.js'
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
            'js/filemanager.js',
            'js/imagemanager.js',
            'js/redactor.de.js',
            'js/editor.js',
            filters='jsmin',
            output='bundles/editor.bundle.js'
        )

        code_editor = Bundle(
            'js/ace.js',
            'js/ace-mode-form.js',
            'js/ace-theme-tomorrow.js',
            'js/code_editor.js',
            filters='jsmin',
            output='bundles/code_editor.bundle.js'
        )

        common = Bundle(
            'js/modernizr.js',
            'js/jquery.js',
            'js/fastclick.js',
            'js/foundation.js',
            'js/intercooler.js',
            'js/underscore.js',
            'js/react.js',
            'js/form_dependencies.js',
            confirm,
            map,
            'js/common.js',
            filters='jsmin',
            output='bundles/common.bundle.js'
        )

        common_theme = Bundle(
            map_theme,
            filters='cssmin',
            output='bundles/common.bundle.css'
        )

        return {
            'code_editor': code_editor,
            'common': common,
            'common_theme': common_theme,
            'dropzone': dropzone,
            'editor': editor,
            'map': map,
            'map_theme': map_theme,
            'redactor': redactor,
            'redactor_theme': redactor_theme
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
