from onegov.core import utils
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs


class FeriennetApp(OrgApp):
    pass


@FeriennetApp.template_directory()
def get_template_directory():
    return 'templates'


@FeriennetApp.setting(section='org', name='enable_user_registration')
def get_enable_user_registration():
    return True


@FeriennetApp.setting(section='org', name='enable_yubikey')
def get_enable_yubikey():
    return False


@FeriennetApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [utils.module_path('onegov.feriennet', 'locale')] \
        + get_org_i18n_localedirs()
