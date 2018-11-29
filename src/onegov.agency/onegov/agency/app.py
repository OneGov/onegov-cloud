from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.initial_content import create_new_organisation
from onegov.agency.theme import AgencyTheme
from onegov.core import utils
from onegov.form import FormApp
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.org.custom import get_global_tools
from onegov.org.models import Organisation
from onegov.org.new_elements import Link
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg


class AgencyApp(OrgApp, FormApp):

    #: the version of this application (do not change manually!)
    version = '0.0.1'

    @property
    def root_pdf_exists(self):
        return self.filestorage.exists('root.pdf')

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


def get_top_navigation(request):
    yield Link(
        text=_("People"),
        url=request.class_link(ExtendedPersonCollection)
    )
    yield Link(
        text=_("Agencies"),
        url=request.class_link(ExtendedAgencyCollection)
    )
    if request.is_manager:
        yield Link(
            text=_("Hidden contents"),
            url=request.class_link(Organisation, name='view-hidden')
        )


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
