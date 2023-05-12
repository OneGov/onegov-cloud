from onegov.core.utils import module_path
from onegov.landsgemeinde.content import create_new_organisation
from onegov.landsgemeinde.custom import get_global_tools
from onegov.landsgemeinde.custom import get_top_navigation
from onegov.landsgemeinde.theme import LandsgemeindeTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_i18n_localedirs as get_i18n_localedirs_base


class LandsgemeindeApp(TownApp):

    pass


@LandsgemeindeApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@LandsgemeindeApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
    }


@LandsgemeindeApp.static_directory()
def get_static_directory():
    return 'static'


@LandsgemeindeApp.template_directory()
def get_template_directory():
    return 'templates'


@LandsgemeindeApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = module_path('onegov.landsgemeinde', 'locale')
    return [mine] + get_i18n_localedirs_base()


@LandsgemeindeApp.setting(section='core', name='theme')
def get_theme():
    return LandsgemeindeTheme()
