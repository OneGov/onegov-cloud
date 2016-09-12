""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from onegov.core import utils
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.town.theme import TownTheme
from onegov.town.initial_content import create_new_organisation


class TownApp(OrgApp):
    pass


@TownApp.static_directory()
def get_static_directory():
    return 'static'


@TownApp.template_directory()
def get_template_directory():
    return 'templates'


@TownApp.setting(section='core', name='theme')
def get_theme():
    return TownTheme()


@TownApp.setting(section='org', name='enable_user_registration')
def get_enable_user_registration():
    return False


@TownApp.setting(section='org', name='enable_yubikey')
def get_enable_yubikey():
    return True


@TownApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [utils.module_path('onegov.town', 'locale')] \
        + get_org_i18n_localedirs()


@TownApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation
