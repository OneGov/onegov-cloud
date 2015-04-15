""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from cached_property import cached_property
from onegov.core import Framework
from onegov.core import utils
from onegov.town.model import Town
from onegov.town.theme import TownTheme
from webassets import Bundle


class TownApp(Framework):
    """ The town application. Include this in your onegov.yml to serve it
    with onegov-server.

    """

    @property
    def theme_options(self):
        # XXX the town is loaded multiple times during one request, even though
        # it rarely changes, even over multiple reqeusts. It would make
        # sense to cache this somewhere and invalidate that cache only when
        # there's a change to the town.
        return self.session().query(Town).first().theme_options or {}

    @cached_property
    def webassets_path(self):
        return utils.module_path('onegov.town', 'assets')

    @cached_property
    def webassets_bundles(self):
        return {
            'common': Bundle(
                'js/modernizr.js',
                'js/jquery.js',
                'js/fastclick.js',
                'js/foundation.js',
                'js/common.js',
                filters='jsmin',
                output='bundles/common.bundle.js'
            ),
            'dropzone': Bundle(
                'js/dropzone.js',
                filters='jsmin',
                output='bundles/dropzone.bundle.js'
            )
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
