from cached_property import cached_property
from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.initial_content import create_new_organisation
from onegov.agency.theme import AgencyTheme
from onegov.core import utils
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as get_org_common_asset
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs


class AgencyApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '0.0.1'

    @cached_property
    def root_pages(self):
        session = self.session()
        people = ExtendedPersonCollection(session)
        people.is_visible = True
        people.title = _("People")
        agencies = ExtendedAgencyCollection(session)
        agencies.is_visible = True
        agencies.title = _("Agencies")
        return (people, agencies)


@AgencyApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@AgencyApp.template_directory()
def get_template_directory():
    return 'templates'


@AgencyApp.setting(section='core', name='theme')
def get_theme():
    return AgencyTheme()


@AgencyApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.agency', 'locale')
    return [mine] + get_org_i18n_localedirs()


@AgencyApp.webasset_path()
def get_js_path():
    return 'assets/js'


@AgencyApp.webasset_path()
def get_css_path():
    return 'assets/css'


@AgencyApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@AgencyApp.webasset(
    'common',
    filters={'css': ['datauri', 'custom-rcssmin']}
)
def get_common_asset():
    yield from get_org_common_asset()
    yield 'chosen.css'
    yield 'chosen.jquery.js'
    yield 'chosen-init.js'
