from more.content_security import UNSAFE_EVAL
from more.content_security import UNSAFE_INLINE
from onegov.core import Framework, utils
from onegov.core.filestorage import FilestorageFile
from onegov.core.framework import default_content_security_policy
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.gazette.models import Principal
from onegov.gazette.theme import GazetteTheme
from onegov.quill import QuillApp
from onegov.user import UserApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from more.content_security import ContentSecurityPolicy


class GazetteApp(Framework, DepotApp, QuillApp, FormApp, UserApp):
    """ The gazette application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    # NOTE: Even though this technically can be None, it never should be
    #       in a valid application, it would be annoying to check for None
    #       everywhere we use this, so we treat it as existing
    @property
    def principal(self) -> Principal:
        """ Returns the principal of the gazette app. See
        :class:`onegov.gazette.models.principal.Principal`.

        """
        return self.cache.get_or_create('principal', self.load_principal)

    def load_principal(self) -> Principal | None:
        """ The principal is defined in the ``principal.yml`` file stored
        on the applications filestorage root.

        If the file does not exist, the site root does not exist and therefore
        a 404 is returned.

        The structure of the yaml file is defined in
        class:`onegov.gazette.model.Principal`.

        """
        assert self.has_filestorage
        fs = self.filestorage
        assert fs is not None

        if fs.isfile('principal.yml'):
            return Principal.from_yaml(
                fs.open('principal.yml', encoding='utf-8').read()
            )
        return None

    @property
    def logo(self) -> FilestorageFile | None:
        """ Returns the logo as
        :class:`onegov.core.filestorage.FilestorageFile`.

        """
        return self.cache.get_or_create('logo', self.load_logo)

    def load_logo(self) -> FilestorageFile | None:
        fs = self.filestorage
        assert fs is not None
        if fs.isfile(self.principal.logo):
            return FilestorageFile(self.principal.logo)
        return None

    @property
    def logo_for_pdf(self) -> str | None:
        """ Returns the SVG logo used for PDFs as string.

        """
        return self.cache.get_or_create('logo_for_pdf', self.load_logo_for_pdf)

    def load_logo_for_pdf(self) -> str | None:
        fs = self.filestorage
        assert fs is not None
        if fs.isfile(self.principal.logo_for_pdf):
            with fs.open(self.principal.logo_for_pdf) as file:
                result = file.read()
            return result
        return None

    @property
    def theme_options(self) -> dict[str, str]:
        assert self.principal.color is not None, """ No color defined, be
        sure to define one in your principal.yml like this:

            color: '#123456'

        Note how you need to add apostrophes around the definition!
        """

        return {
            'primary-color': self.principal.color
        }


@GazetteApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@GazetteApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@GazetteApp.setting(section='core', name='theme')
def get_theme() -> GazetteTheme:
    return GazetteTheme()


@GazetteApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.gazette', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@GazetteApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH'}


@GazetteApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@GazetteApp.setting(section='content_security_policy', name='default')
def get_content_security_policy() -> 'ContentSecurityPolicy':
    policy = default_content_security_policy()
    policy.script_src.remove(UNSAFE_EVAL)
    policy.script_src.remove(UNSAFE_INLINE)
    return policy


@GazetteApp.webasset_path()
def get_shared_assets_path() -> str:
    return utils.module_path('onegov.shared', 'assets/js')


@GazetteApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@GazetteApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@GazetteApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@GazetteApp.webasset(
    'frameworks',
    filters={'css': ['datauri', 'custom-rcssmin']}
)
def get_frameworks_asset() -> 'Iterator[str]':
    # common assets unlikely to change
    yield 'modernizr.js'

    # jQuery
    yield 'jquery.js'
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.full.js'

    # other frameworks
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'stacktable.js'
    yield 'sortable.js'
    yield 'sortable_custom.js'
    yield 'dropzone.js'

    # utils
    yield 'url.js'


@GazetteApp.webasset('common')
def get_common_asset() -> 'Iterator[str]':
    # custom code
    yield 'form_dependencies.js'
    yield 'datetimepicker.js'
    yield 'common.js'
