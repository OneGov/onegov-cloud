from onegov.core.utils import module_path
from onegov.pas.content import create_new_organisation
from onegov.pas.custom import get_global_tools
from onegov.pas.custom import get_top_navigation
from onegov.pas.theme import PasTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_i18n_localedirs as get_i18n_localedirs_base


class PasApp(TownApp):

    pass


@PasApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@PasApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
    }


@PasApp.static_directory()
def get_static_directory():
    return 'static'


@PasApp.template_directory()
def get_template_directory():
    return 'templates'


# @PasApp.webasset_path()
# def get_js_path():
#     return 'assets/js'


@PasApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = module_path('onegov.pas', 'locale')
    return [mine] + get_i18n_localedirs_base()


@PasApp.setting(section='core', name='theme')
def get_theme():
    return PasTheme()
