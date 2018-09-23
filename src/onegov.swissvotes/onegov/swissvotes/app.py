from cached_property import cached_property
from onegov.core import Framework
from onegov.core import utils
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.quill import QuillApp
from onegov.search import ElasticsearchApp
from onegov.swissvotes.models import Principal
from onegov.swissvotes.theme import SwissvotesTheme


class SwissvotesApp(Framework, FormApp, QuillApp, DepotApp, ElasticsearchApp):
    """ The swissvotes application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    def configure_sentry(self, **cfg):
        self.sentry_js = cfg.get('sentry_js')

    @cached_property
    def principal(self):
        return Principal()


@SwissvotesApp.static_directory()
def get_static_directory():
    return 'static'


@SwissvotesApp.template_directory()
def get_template_directory():
    return 'templates'


@SwissvotesApp.setting(section='core', name='theme')
def get_theme():
    return SwissvotesTheme()


@SwissvotesApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.swissvotes', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@SwissvotesApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH', 'fr_CH', 'en_US'}


@SwissvotesApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@SwissvotesApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@SwissvotesApp.webasset_path()
def get_js_path():
    return 'assets/js'


@SwissvotesApp.webasset_path()
def get_css_path():
    return 'assets/css'


@SwissvotesApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@SwissvotesApp.webasset('common')
def get_common_asset():
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'jquery.tablesorter.js'
    yield 'tablesaw.css'
    yield 'tablesaw.jquery.js'
    yield 'tablesaw-create.js'
    yield 'tablesaw-init.js'
    yield 'chosen.css'
    yield 'chosen.jquery.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'form_dependencies.js'
    yield 'common.js'
