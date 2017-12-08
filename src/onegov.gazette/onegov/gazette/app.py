from onegov.core import Framework, utils
from onegov.core.filestorage import FilestorageFile
from onegov.file import DepotApp
from onegov.gazette.models import Principal
from onegov.gazette.theme import GazetteTheme
from onegov.quill import QuillApp


class GazetteApp(Framework, DepotApp, QuillApp):
    """ The gazette application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    @property
    def principal(self):
        """ Returns the principal of the gazette app. See
        :class:`onegov.gazette.models.principal.Principal`.

        """
        return self.cache.get_or_create('principal', self.load_principal)

    def load_principal(self):
        """ The principal is defined in the ``principal.yml`` file stored
        on the applications filestorage root.

        If the file does not exist, the site root does not exist and therefore
        a 404 is returned.

        The structure of the yaml file is defined in
        class:`onegov.gazette.model.Principal`.

        """
        assert self.has_filestorage

        if self.filestorage.isfile('principal.yml'):
            return Principal.from_yaml(
                self.filestorage.open('principal.yml', encoding='utf-8').read()
            )

    @property
    def logo(self):
        """ Returns the logo as
        :class:`onegov.core.filestorage.FilestorageFile`.

        """
        return self.cache.get_or_create('logo', self.load_logo)

    def load_logo(self):
        if self.filestorage.isfile(self.principal.logo):
            return FilestorageFile(self.principal.logo)

    @property
    def theme_options(self):
        assert self.principal.color is not None, """ No color defined, be
        sure to define one in your principal.yml like this:

            color: '#123456'

        Note how you need to add apostrophes around the definition!
        """

        return {
            'primary-color': self.principal.color
        }

    def configure_sentry(self, **cfg):
        self.sentry_js = cfg.get('sentry_js')


@GazetteApp.static_directory()
def get_static_directory():
    return 'static'


@GazetteApp.template_directory()
def get_template_directory():
    return 'templates'


@GazetteApp.setting(section='core', name='theme')
def get_theme():
    return GazetteTheme()


@GazetteApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.gazette', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@GazetteApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH'}


@GazetteApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@GazetteApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@GazetteApp.webasset_path()
def get_js_path():
    return 'assets/js'


@GazetteApp.webasset_path()
def get_css_path():
    return 'assets/css'


@GazetteApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@GazetteApp.webasset(
    'frameworks',
    filters={'css': ['datauri', 'custom-rcssmin']}
)
def get_frameworks_asset():
    # common assets unlikely to change
    yield 'modernizr.js'

    # jQuery
    yield 'jquery.js'
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.full.js'

    # other frameworks
    yield 'fastclick.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'stacktable.js'
    yield 'chosen.css'
    yield 'chosen.jquery.js'
    yield 'sortable.js'
    yield 'sortable_custom.js'
    yield 'dropzone.js'


@GazetteApp.webasset('common')
def get_common_asset():
    # custom code
    yield 'form_dependencies.js'
    yield 'datetimepicker.js'
    yield 'common.js'
