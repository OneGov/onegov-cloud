from onegov.activity import Period, PeriodCollection
from onegov.core.orm import orm_cached
from onegov.core import utils
from onegov.feriennet.initial_content import create_new_organisation
from onegov.feriennet.request import FeriennetRequest
from onegov.feriennet.theme import FeriennetTheme
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.org.app import get_common_asset as get_org_common_asset


class FeriennetApp(OrgApp):

    request_class = FeriennetRequest

    def es_may_use_private_search(self, request):
        return request.is_admin

    @orm_cached(policy='on-table-change:periods')
    def active_period(self):
        return PeriodCollection(self.session()).active()

    @orm_cached(policy='on-table-change:periods')
    def periods(self):
        p = PeriodCollection(self.session()).query()
        p = p.order_by(Period.execution_start)

        return p


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


@FeriennetApp.setting(section='org', name='status_mail_roles')
def get_status_mail_roles():
    return ('admin', )


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


@FeriennetApp.webasset_path()
def get_js_path():
    return 'assets/js'


@FeriennetApp.webasset('common')
def get_common_asset():
    yield from get_org_common_asset()
    yield 'reloadfrom.js'
    yield 'printthis.js'
    yield 'print.js'
    yield 'many.jsx'
