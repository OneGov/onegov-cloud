import re

from dectate import directive
from more.content_security import NONE
from more.content_security import SELF
from more.content_security import UNSAFE_EVAL
from more.content_security import UNSAFE_INLINE
from more.content_security.core import content_security_policy_tween_factory
from onegov.core import Framework
from onegov.core import utils
from onegov.core.filestorage import FilestorageFile
from onegov.core.framework import current_language_tween_factory
from onegov.core.framework import default_content_security_policy
from onegov.core.framework import transaction_tween_factory
from onegov.election_day.directives import CsvFileAction
from onegov.election_day.directives import JsonFileAction
from onegov.election_day.directives import ManageFormAction
from onegov.election_day.directives import ManageHtmlAction
from onegov.election_day.directives import PdfFileViewAction
from onegov.election_day.directives import ScreenWidgetAction
from onegov.election_day.directives import SvgFileViewAction
from onegov.election_day.directives import XmlFileAction
from onegov.election_day.models import Principal
from onegov.election_day.request import ElectionDayRequest
from onegov.election_day.theme import ElectionDayTheme
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.user import UserApp
from onegov.websockets import WebsocketsApp


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from more.content_security import ContentSecurityPolicy
    from onegov.core.cache import RedisCacheRegion
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from webob import Response


class ElectionDayApp(Framework, FormApp, UserApp, DepotApp, WebsocketsApp):
    """ The election day application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True
    request_class = ElectionDayRequest

    csv_file = directive(CsvFileAction)
    json_file = directive(JsonFileAction)
    xml_file = directive(XmlFileAction)
    manage_form = directive(ManageFormAction)
    manage_html = directive(ManageHtmlAction)
    pdf_file = directive(PdfFileViewAction)
    svg_file = directive(SvgFileViewAction)
    screen_widget = directive(ScreenWidgetAction)

    # FIXME: Technically this can be None as well, but since we 404
    #        if we don't have a principal we pretend it's always there
    #        for now this is easier than having assert self.principal
    #        everywhere
    @property
    def principal(self) -> 'Canton | Municipality':
        """ Returns the principal of the election day app. See
        :class:`onegov.election_day.models.principal.Principal`.

        """
        return self.cache.get_or_create('principal', self.load_principal)

    def load_principal(self) -> 'Canton | Municipality | None':
        """ The principal is defined in the ``principal.yml`` file stored
        on the applications filestorage root.

        If the file does not exist, the site root does not exist and therefore
        a 404 is returned.

        The structure of the yaml file is defined in
        class:`onegov.election_app.model.Principal`.

        """
        fs = self.filestorage
        assert fs is not None

        if not fs.isfile('principal.yml'):
            return None

        return Principal.from_yaml(
            fs.open('principal.yml', encoding='utf-8').read()
        )

    @property
    def logo(self) -> FilestorageFile | None:
        """ Returns the logo as
        :class:`onegov.core.filestorage.FilestorageFile`.

        """
        return self.cache.get_or_create('logo', self.load_logo)

    def load_logo(self) -> FilestorageFile | None:
        logo = self.principal.logo
        if logo and self.filestorage.isfile(logo):  # type:ignore[union-attr]
            return FilestorageFile(logo)
        return None

    @property
    def theme_options(self) -> dict[str, Any]:
        color = self.principal.color
        assert color is not None, """ No color defined, be
        sure to define one in your principal.yml like this:

            color: '#123456'

        Note how you need to add apostrophes around the definition!
        """

        return {'primary-color': color}

    @property
    def pages_cache(self) -> 'RedisCacheRegion':
        """ A cache for pages. """
        expiration_time = 300
        if self.principal and hasattr(self.principal, 'cache_expiration_time'):
            expiration_time = self.principal.cache_expiration_time
        return self.get_cache('pages', expiration_time)


@ElectionDayApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@ElectionDayApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@ElectionDayApp.setting(section='core', name='theme')
def get_theme() -> ElectionDayTheme:
    return ElectionDayTheme()


@ElectionDayApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.election_day', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@ElectionDayApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH', 'fr_CH', 'it_CH', 'rm_CH'}


@ElectionDayApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@ElectionDayApp.setting(section='content_security_policy', name='default')
def org_content_security_policy() -> 'ContentSecurityPolicy':
    policy = default_content_security_policy()
    policy.script_src.remove(UNSAFE_EVAL)
    policy.script_src.remove(UNSAFE_INLINE)
    return policy


@ElectionDayApp.tween_factory(under=content_security_policy_tween_factory)
def enable_iframes_and_analytics_tween_factory(
    app: ElectionDayApp,
    handler: 'Callable[[ElectionDayRequest], Response]'
) -> 'Callable[[ElectionDayRequest], Response]':

    no_iframe_paths = (
        r'/auth/.*',
        r'/manage/.*'
    )
    no_iframe_paths_re = re.compile(rf"({'|'.join(no_iframe_paths)})")

    iframe_paths = (
        r'/ballot/.*',
        r'/vote/.*',
        r'/election/.*',
        r'/elections/.*',
        r'/elections-part/.*',
        r'/screen/.*',
    )
    iframe_paths_re = re.compile(rf"({'|'.join(iframe_paths)})")

    def enable_iframes_and_analytics_tween(
        request: ElectionDayRequest
    ) -> 'Response':
        """ Enables iframes and analytics. """

        result = handler(request)

        if no_iframe_paths_re.match(request.path_info or '/'):
            request.content_security_policy.frame_ancestors = {NONE}
        elif iframe_paths_re.match(request.path_info or '/'):
            request.content_security_policy.frame_ancestors.add('http://*')
            request.content_security_policy.frame_ancestors.add('https://*')

        request.content_security_policy.connect_src.add(SELF)
        if app.principal:
            for domain in getattr(app.principal, 'csp_script_src', []):
                request.content_security_policy.script_src.add(domain)
            for domain in getattr(app.principal, 'csp_connect_src', []):
                request.content_security_policy.connect_src.add(domain)

        return result

    return enable_iframes_and_analytics_tween


@ElectionDayApp.tween_factory(over=current_language_tween_factory)
def override_language_tween_factory(
    app: ElectionDayApp,
    handler: 'Callable[[ElectionDayRequest], Response]'
) -> 'Callable[[ElectionDayRequest], Response]':
    def override_language_tween(request: ElectionDayRequest) -> 'Response':
        """ Allows the current language to be overwritten using a query
        parameter.

        """

        locale = request.params.get('locale')
        if locale in app.locales:
            request.locale = locale  # type:ignore[assignment]

        return handler(request)

    return override_language_tween


@ElectionDayApp.tween_factory(
    under=override_language_tween_factory,
    over=transaction_tween_factory
)
def cache_control_tween_factory(
    app: ElectionDayApp,
    handler: 'Callable[[ElectionDayRequest], Response]'
) -> 'Callable[[ElectionDayRequest], Response]':

    def cache_control_tween(request: ElectionDayRequest) -> 'Response':
        """ Set headers and cookies for cache control.

        Makes sure, pages are not cached downstream when logged in by setting
        the cache-control header accordingly.

        Sets `no_cache` cookie which can be used for bypassing a downstream
        cache.

        """

        response = handler(request)
        if request.is_logged_in:
            response.headers.add('cache-control', 'no-store')
            if request.cookies.get('no_cache', '0') == '0':
                response.set_cookie(
                    'no_cache',
                    '1',
                    # TODO: This is fixed upstream, should be able to
                    #       get rid of this type-ignore soon
                    samesite='Lax'  # type:ignore[arg-type]
                )
        else:
            if request.cookies.get('no_cache', '0') == '1':
                response.delete_cookie('no_cache')

        return response

    return cache_control_tween


@ElectionDayApp.tween_factory(
    under=override_language_tween_factory,
    over=transaction_tween_factory
)
def micro_cache_anonymous_pages_tween_factory(
    app: ElectionDayApp,
    handler: 'Callable[[ElectionDayRequest], Response]'
) -> 'Callable[[ElectionDayRequest], Response]':

    cache_paths = (
        '/ballot/.*',
        '/vote/.*',
        '/election/.*',
        '/elections/.*',
        '/elections-part/.*',
        '/screen/.*',
        '/catalog.rdf',
        '/sitemap',
        '/sitemap.xml',
    )
    cache_paths_re = re.compile(r'^({})$'.format('|'.join(cache_paths)))

    def should_cache_fn(response: 'Response') -> bool:
        return (
            response.status_code == 200
            and 'Set-Cookie' not in response.headers
        )

    def micro_cache_anonymous_pages_tween(
        request: ElectionDayRequest
    ) -> 'Response':
        """ Cache all pages for 5 minutes. """

        # do not cache POST, DELETE etc.
        if request.method not in ('GET', 'HEAD'):
            return handler(request)

        # no cache if the user is logged in
        if request.is_logged_in:
            return handler(request)

        # only cache whitelisted paths
        if not cache_paths_re.match(request.path_info or '/'):
            return handler(request)

        if request.method == 'HEAD':
            # HEAD requests are cached with only the path
            key = ':'.join((request.method, request.path))
        else:
            # each page is cached once per request method, host, path including
            # query string, language and headerless/headerful (and by
            # application id as the pages_cache is bound to it)
            key = ':'.join((
                request.method,
                request.host,
                request.path_qs,
                request.locale or '',
                'hl' if 'headerless' in request.browser_session else 'hf'
            ))

        return app.pages_cache.get_or_create(
            key,
            creator=lambda: handler(request),
            should_cache_fn=should_cache_fn
        )

    return micro_cache_anonymous_pages_tween


@ElectionDayApp.webasset_path()
def get_shared_assets_path() -> str:
    return utils.module_path('onegov.shared', 'assets/js')


@ElectionDayApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@ElectionDayApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@ElectionDayApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@ElectionDayApp.webasset('common')
def get_common_asset() -> 'Iterator[str]':
    # Common assets unlikely to change
    yield 'modernizr.js'

    # jQuery
    yield 'jquery.js'
    yield 'jquery.tablesorter.js'
    yield 'jquery.tablesorter.staticRow.js'

    # D3
    yield 'd3.js'
    yield 'topojson.js'
    yield 'd3.tip.js'
    yield 'd3.sankey.js'

    # Tablesaw
    yield 'tablesaw.css'
    yield 'tablesaw.jquery.js'
    yield 'tablesaw-translations.js'
    yield 'tablesaw-init.js'

    # other frameworks
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'iframeResizer.contentWindow.js'


@ElectionDayApp.webasset('custom')
def get_custom_asset() -> 'Iterator[str]':
    # common code
    yield 'common.js'

    # D3 charts and maps
    yield 'd3.chart.bar.js'
    yield 'd3.chart.grouped.js'
    yield 'd3.chart.sankey.js'
    yield 'd3.map.districts.js'
    yield 'd3.map.entities.js'

    # Chart initalization
    yield 'charts-init.js'
    yield 'embed.js'

    # Embedded tables as widgets
    yield 'embedded_widgets.js'

    # Form
    yield 'error-focus.js'

    # notifications
    yield 'notifications.js'


@ElectionDayApp.webasset('backend_common')
def get_backend_common_asset() -> 'Iterator[str]':
    # Common assets unlikely to change, only used in the backend
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'form_dependencies.js'
    yield 'doubleclick.js'


@ElectionDayApp.webasset('screen')
def get_screen_asset() -> 'Iterator[str]':
    # Code used for screen update
    yield 'screen.js'
