""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from onegov.core import Framework
from onegov.core import utils


class TownApp(Framework):
    """ The town application. Include this in your onegov.yml to serve it
    with onegov-server.

    """


@TownApp.template_directory()
def get_template_directory():
    return 'templates'


@TownApp.setting(section='i18n', name='domain')
def get_i18n_domain():
    return 'onegov.town'


@TownApp.setting(section='i18n', name='localedir')
def get_i18n_localedir():
    return utils.module_path('onegov.town', 'locale')


@TownApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de'
