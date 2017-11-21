import os
import re

from datetime import datetime
from dectate import directive
from onegov.core import Framework
from onegov.core import utils
from onegov.core.datamanager import FileDataManager
from onegov.core.filestorage import FilestorageFile
from onegov.core.framework import transaction_tween_factory
from onegov.election_day.directives import ManageFormAction
from onegov.election_day.directives import ManageHtmlAction
from onegov.election_day.models import Principal
from onegov.election_day.theme import ElectionDayTheme


class ElectionDayApp(Framework):
    """ The election day application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True
    manage_html = directive(ManageHtmlAction)
    manage_form = directive(ManageFormAction)

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

    def send_sms(self, receiver=None, content=None):
        """ Sends an SMS by writing a file to the `sms_directory` of the
        principal.

        SMS sent through this method are bound to the current transaction.
        If that transaction is aborted or not commited, the SMS is not sent.

        Usually you'll use this method inside a request, where transactions
        are automatically commited at the end.

        """
        path = os.path.join(self.configuration['sms_directory'], self.schema)
        if not os.path.exists(path):
            os.makedirs(path)

        path = os.path.join(
            path, '{}.{}'.format(receiver, datetime.now().timestamp())
        )

        try:
            content = content.encode('utf-8')
        except AttributeError:
            pass

        FileDataManager.write_file(content, path)

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

    @property
    def pages_cache(self):
        """ A five minute cache for pages. """
        return self.get_cache(self.application_id + ':5m', expiration_time=300)

    def configure_sentry(self, **cfg):
        self.sentry_js = cfg.get('sentry_js')


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


@ElectionDayApp.tween_factory(over=transaction_tween_factory)
def micro_cache_anonymous_pages_tween_factory(app, handler):

    cache_paths = (
        '/ballot/.*',
        '/vote/.*',
        '/votes/.*',
        '/election/.*',
        '/elections/.*',
        '/catalog.rdf',
    )

    cache_paths = re.compile(r'^({})$'.format('|'.join(cache_paths)))

    def micro_cache_anonymous_pages_tween(request):
        """ Cache all pages for 5 minutes.

        Logged in users are exempt of this cache. If a user wants to manually
        bust the cache he or she just needs to refresh the cached page using
        Shift + F5 as an anonymous user.

        That is to say, we observe the Cache-Control header.

        """

        # no cache if the user is logged in
        if request.is_logged_in:
            return handler(request)

        # only cache whitelisted paths
        if not cache_paths.match(request.path_info):
            return handler(request)

        # allow cache busting through browser shift+f5
        if request.headers.get('cache-control') == 'no-cache':
            return handler(request)

        # each page is cached once per language and headerless/headerful
        # (and by application id as the pages_cache is bound to it)
        mode = 'headerless' in request.browser_session and 'hl' or 'hf'
        key = ':'.join((request.locale, request.path_info, mode))

        return app.pages_cache.get_or_create(
            key,
            creator=lambda: handler(request),
            should_cache_fn=lambda response: response.status_code == 200
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

    # other frameworks
    yield 'fastclick.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'stacktable.js'
    yield 'iframeResizer.contentWindow.js'


@ElectionDayApp.webasset('custom')
def get_custom_asset():
    # common code
    yield 'common.js'

    # D3 charts
    yield 'd3.chart.bar.js'
    yield 'd3.chart.grouped.js'
    yield 'd3.chart.map.js'
    yield 'd3.chart.sankey.js'

    # Chart initalization
    yield 'embed.js'
    yield 'charts.js'
    yield 'ballot-map.js'


@ElectionDayApp.webasset('backend_common')
def get_backend_common_asset():
    # Common assets unlikely to change, only used in the backend
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'form_dependencies.js'
