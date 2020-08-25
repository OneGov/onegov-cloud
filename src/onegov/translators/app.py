from onegov.core import utils, Framework
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.gis import MapboxApp
from onegov.org import OrgApp
from onegov.search import ElasticsearchApp
from onegov.translators.theme.translators_theme import TranslatorAppTheme
from onegov.user import UserApp


class TranslatorApp(
    Framework, ElasticsearchApp, MapboxApp, DepotApp, FormApp, UserApp):

    serve_static_files = True

    def es_may_use_private_search(self, request):
        return request.is_admin


@TranslatorApp.template_directory()
def get_template_directory():
    return 'templates'


@OrgApp.static_directory()
def get_static_directory():
    return 'static'


@TranslatorApp.setting(section='core', name='theme')
def get_theme():
    return TranslatorAppTheme()


@TranslatorApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.translators', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')

    ]


@TranslatorApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH'}


@TranslatorApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@TranslatorApp.webasset_path()
def get_js_path():
    return 'assets/js'


@TranslatorApp.webasset_path()
def get_css_path():
    return 'assets/css'


@TranslatorApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@TranslatorApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@TranslatorApp.webasset(
    'frameworks',
    filters={'css': ['datauri', 'custom-rcssmin']}
)
def get_frameworks_asset():
    # common assets unlikely to change
    yield 'modernizr.js'

    # jQuery
    yield 'jquery.js'

    # other frameworks
    yield 'foundation.js'


@TranslatorApp.webasset('common')
def get_common_asset():
    yield 'translators.js'


@TranslatorApp.webasset('common')
def get_common_asset():
    # custom code
    yield 'form_dependencies.js'
