from cached_property import cached_property
from onegov.core import Framework
from onegov.core import utils
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.wtfs.models import Principal
from onegov.wtfs.theme import WtfsTheme


class WtfsApp(Framework, FormApp, DepotApp):
    """ The Wtfs application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    def configure_sentry(self, **cfg):
        self.sentry_js = cfg.get('sentry_js')

    @cached_property
    def principal(self):
        return Principal()

    def add_initial_content(self):
        pass


@WtfsApp.static_directory()
def get_static_directory():
    return 'static'


@WtfsApp.template_directory()
def get_template_directory():
    return 'templates'


@WtfsApp.setting(section='core', name='theme')
def get_theme():
    return WtfsTheme()


@WtfsApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.wtfs', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@WtfsApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH'}


@WtfsApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@WtfsApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@WtfsApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WtfsApp.webasset_path()
def get_css_path():
    return 'assets/css'


@WtfsApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@WtfsApp.webasset('frameworks')
def get_frameworks_asset():
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'jquery.tablesorter.js'
    yield 'tablesaw.css'
    yield 'tablesaw.jquery.js'
    yield 'tablesaw-create.js'
    yield 'tablesaw-init.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'react.js'
    yield 'react-dom.js'
    yield 'react-dropdown-tree-select.js'
    yield 'react-dropdown-tree-select.css'
    yield 'form_dependencies.js'


@WtfsApp.webasset('common')
def get_common_asset():
    yield 'common.js'
