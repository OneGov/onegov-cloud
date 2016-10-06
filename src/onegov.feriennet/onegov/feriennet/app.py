from onegov.core import utils
from onegov.feriennet.initial_content import create_new_organisation
from onegov.feriennet.request import FeriennetRequest
from onegov.feriennet.theme import FeriennetTheme
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs


class FeriennetApp(OrgApp):

    request_class = FeriennetRequest

    def es_may_use_private_search(self, request):
        return request.is_admin


@FeriennetApp.template_directory()
def get_template_directory():
    return 'templates'


@FeriennetApp.setting(section='org', name='enable_user_registration')
def get_enable_user_registration():
    return True


@FeriennetApp.setting(section='org', name='enable_yubikey')
def get_enable_yubikey():
    return False


@FeriennetApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@FeriennetApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [utils.module_path('onegov.feriennet', 'locale')] \
        + get_org_i18n_localedirs()


@FeriennetApp.setting(section='core', name='theme')
def get_theme():
    return FeriennetTheme()


@FeriennetApp.static_directory()
def get_static_directory():
    return 'static'
