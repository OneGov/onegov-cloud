import json
import os
import re

from datetime import datetime
from dectate import directive
from more.content_security import NONE
from more.content_security import SELF
from more.content_security.core import content_security_policy_tween_factory
from onegov.core import Framework
from onegov.core import utils
from onegov.core.datamanager import FileDataManager
from onegov.core.filestorage import FilestorageFile
from onegov.core.framework import current_language_tween_factory
from onegov.core.framework import transaction_tween_factory
from onegov.core.utils import batched
from onegov.election_day.directives import CsvFileAction
from onegov.election_day.directives import JsonFileAction
from onegov.election_day.directives import ManageFormAction
from onegov.election_day.directives import ManageHtmlAction
from onegov.election_day.directives import PdfFileViewAction
from onegov.election_day.directives import ScreenWidgetAction
from onegov.election_day.directives import SvgFileViewAction
from onegov.election_day.models import Principal
from onegov.election_day.theme import ElectionDayTheme
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.user import UserApp
from onegov.websockets import WebsocketsApp


class ElectionDayApp(Framework, FormApp, UserApp, DepotApp, WebsocketsApp):
    """ The election day application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True
    csv_file = directive(CsvFileAction)
    json_file = directive(JsonFileAction)
    manage_form = directive(ManageFormAction)
    manage_html = directive(ManageHtmlAction)
    pdf_file = directive(PdfFileViewAction)
    svg_file = directive(SvgFileViewAction)
    screen_widget = directive(ScreenWidgetAction)

    @property
    def principal(self):
        """ Returns the principal of the election day app. See
        :class:`onegov.election_day.models.principal.Principal`.

        """
        return self.cache.get_or_create('principal', self.load_principal)

    def load_principal(self):
        """ The principal is defined in the ``principal.yml`` file stored
        on the applications filestorage root.

        If the file does not exist, the site root does not exist and therefore
        a 404 is returned.

        The structure of the yaml file is defined in
        class:`onegov.election_app.model.Principal`.

        """
        assert self.has_filestorage

        if self.filestorage.isfile('principal.yml'):
            return Principal.from_yaml(
                self.filestorage.open('principal.yml', encoding='utf-8').read()
            )

    def send_sms(self, receivers=None, content=None):
        """ Sends an SMS by writing a file to the `sms_directory` of the
        principal.

        receivers can be a single phone number or a collection of numbers.
        Delivery will be split into multiple batches if the number of receivers
        exceeds 1000, this is due to a limit in the ASPSMS API. This also means
        more than one file is written in such cases. They will share the same
        timestamp but will have a batch number prefixed.

        SMS sent through this method are bound to the current transaction.
        If that transaction is aborted or not commited, the SMS is not sent.

        Usually you'll use this method inside a request, where transactions
        are automatically commited at the end.

        """
        path = os.path.join(self.configuration['sms_directory'], self.schema)
        if not os.path.exists(path):
            os.makedirs(path)

        if isinstance(receivers, str):
            receivers = [receivers]

        if isinstance(content, bytes):
            # NOTE: This will fail if we want to be able to send
            #       arbitrary bytes. We could put an errors='ignore'
            #       on this. But it's probably better if we fail.
            #       If we need to be able to send arbitrary bytes
            #       we would need to encode the content in some
            #       other way, e.g. base64, but since ASPSMS is a
            #       JSON API this probably is not possible anyways.
            content = content.decode('utf-8')

        timestamp = datetime.now().timestamp()

        for index, receiver_batch in enumerate(batched(receivers, 1000)):
            payload = json.dumps({
                'receivers': receiver_batch,
                'content': content
            }).encode('utf-8')

            dest_path = os.path.join(
                path, '{}.{}.{}'.format(index, len(receiver_batch), timestamp)
            )

            FileDataManager.write_file(payload, dest_path)

    @property
    def logo(self):
        """ Returns the logo as
        :class:`onegov.core.filestorage.FilestorageFile`.

        """
        return self.cache.get_or_create('logo', self.load_logo)

    def load_logo(self):
        logo = self.principal.logo
        if logo and self.filestorage.isfile(logo):
            return FilestorageFile(logo)

    @property
    def theme_options(self):
        color = self.principal.color
        assert color is not None, """ No color defined, be
        sure to define one in your principal.yml like this:

            color: '#123456'

        Note how you need to add apostrophes around the definition!
        """

        return {'primary-color': color}

    @property
    def pages_cache(self):
        """ A cache for pages. """
        expiration_time = 300
        if self.principal and hasattr(self.principal, 'cache_expiration_time'):
            expiration_time = self.principal.cache_expiration_time
        return self.get_cache('pages', expiration_time)


@ElectionDayApp.static_directory()
def get_static_directory():
    return 'static'


@ElectionDayApp.template_directory()
def get_template_directory():
    return 'templates'


@ElectionDayApp.setting(section='core', name='theme')
def get_theme():
    return ElectionDayTheme()


@ElectionDayApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.election_day', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@ElectionDayApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH', 'fr_CH', 'it_CH', 'rm_CH'}


@ElectionDayApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@ElectionDayApp.tween_factory(
    under=content_security_policy_tween_factory
)
def enable_iframes_and_analytics_tween_factory(app, handler):
    no_iframe_paths = (
        r'/auth/.*',
        r'/manage/.*'
    )
    no_iframe_paths = re.compile(rf"({'|'.join(no_iframe_paths)})")

    iframe_paths = (
        r'/ballot/.*',
        r'/vote/.*',
        r'/election/.*',
        r'/elections/.*',
        r'/elections-part/.*',
        r'/screen/.*',
    )
    iframe_paths = re.compile(rf"({'|'.join(iframe_paths)})")

    def enable_iframes_and_analytics_tween(request):
        """ Enables iframes and analytics. """

        result = handler(request)

        if no_iframe_paths.match(request.path_info):
            request.content_security_policy.frame_ancestors = {NONE}
        elif iframe_paths.match(request.path_info):
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


@ElectionDayApp.tween_factory(
    under=current_language_tween_factory,
    over=transaction_tween_factory
)
def cache_control_tween_factory(app, handler):

    def cache_control_tween(request):
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
                response.set_cookie('no_cache', '1', samesite='Lax')
        else:
            if request.cookies.get('no_cache', '0') == '1':
                response.delete_cookie('no_cache')

        return response

    return cache_control_tween


@ElectionDayApp.tween_factory(
    under=current_language_tween_factory,
    over=transaction_tween_factory
)
def micro_cache_anonymous_pages_tween_factory(app, handler):

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
    cache_paths = re.compile(r'^({})$'.format('|'.join(cache_paths)))

    def should_cache_fn(response):
        return (
            response.status_code == 200
            and 'Set-Cookie' not in response.headers
        )

    def micro_cache_anonymous_pages_tween(request):
        """ Cache all pages for 5 minutes.

        Logged in users are exempt of this cache. If a user wants to manually
        bust the cache he or she just needs to refresh the cached page using
        Shift + F5 as an anonymous user.

        That is to say, we observe the Cache-Control header.

        """

        # do not cache HEAD, POST, DELETE etc.
        if request.method != 'GET':
            return handler(request)

        # no cache if the user is logged in
        if request.is_logged_in:
            return handler(request)

        # only cache whitelisted paths
        if not cache_paths.match(request.path_info):
            return handler(request)

        # allow cache busting through browser shift+f5
        if request.headers.get('cache-control') == 'no-cache':
            return handler(request)

        # each page is cached once per request method, language and
        # headerless/headerful (and by application id as the pages_cache is
        # bound to it)
        key = ':'.join((
            request.method,
            request.locale,
            request.path_qs,
            'hl' if 'headerless' in request.browser_session else 'hf'
        ))

        return app.pages_cache.get_or_create(
            key,
            creator=lambda: handler(request),
            should_cache_fn=should_cache_fn
        )

    return micro_cache_anonymous_pages_tween


@ElectionDayApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@ElectionDayApp.webasset_path()
def get_js_path():
    return 'assets/js'


@ElectionDayApp.webasset_path()
def get_css_path():
    return 'assets/css'


@ElectionDayApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@ElectionDayApp.webasset('common')
def get_common_asset():
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
    yield 'tablesaw-init.js'

    # other frameworks
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'iframeResizer.contentWindow.js'


@ElectionDayApp.webasset('custom')
def get_custom_asset():
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


@ElectionDayApp.webasset('backend_common')
def get_backend_common_asset():
    # Common assets unlikely to change, only used in the backend
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'form_dependencies.js'
    yield 'doubleclick.js'
