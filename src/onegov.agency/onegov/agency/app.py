from onegov.agency.custom import get_global_tools
from onegov.agency.custom import get_top_navigation
from onegov.agency.initial_content import create_new_organisation
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg
from onegov.agency.theme import AgencyTheme
from onegov.core import utils
from onegov.form import FormApp
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs


class AgencyApp(OrgApp, FormApp):

    #: the version of this application (do not change manually!)
    version = '0.0.1'

    @property
    def root_pdf_exists(self):
        return self.filestorage.exists('root.pdf')

    @property
    def root_pdf_modified(self):
        if self.root_pdf_exists:
            return self.filestorage.getdetails('root.pdf').modified

    @property
    def root_pdf(self):
        result = None
        if self.filestorage.exists('root.pdf'):
            with self.filestorage.open('root.pdf', 'rb') as file:
                result = file.read()
        return result

    @root_pdf.setter
    def root_pdf(self, value):
        with self.filestorage.open('root.pdf', 'wb') as file:
            file.write(value.read())

    @property
    def pdf_class(self):
        pdf_layout = self.org.meta.get('pdf_layout')
        if pdf_layout == 'ar':
            return AgencyPdfAr
        if pdf_layout == 'zg':
            return AgencyPdfZg
        return AgencyPdfDefault

    @property
    def enable_yubikey(self):
        return self.org.meta.get('enable_yubikey', self._enable_yubikey)

    @enable_yubikey.setter
    def enable_yubikey(self, value):
        self._enable_yubikey = value


@AgencyApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@AgencyApp.template_directory()
def get_template_directory():
    return 'templates'


@AgencyApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
    }


@AgencyApp.setting(section='core', name='theme')
def get_theme():
    return AgencyTheme()


@AgencyApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.agency', 'locale')
    return [mine] + get_org_i18n_localedirs()


@AgencyApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@AgencyApp.webasset_path()
def get_js_path():
    return 'assets/js'


@AgencyApp.webasset('people-select')
def get_people_select_asset():
    yield 'people-select.js'


@AgencyApp.webasset('sortable-multi-checkbox')
def get_sortable_multi_checkbox_asset():
    yield 'jquery.js'
    yield 'sortable.js'
    yield 'sortable-multi-checkbox.js'
