import re

from cached_property import cached_property
from onegov.core import Framework, utils
from onegov.core.framework import transaction_tween_factory
from onegov.core.filestorage import FilestorageFile
from onegov.shared import asset
from onegov.election_day.theme import ElectionDayTheme
from onegov.election_day.models import Principal
from webassets import Bundle


class ElectionDayApp(Framework):
    """ The election day application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

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
        """ A one minute cache for pages. """
        return self.get_cache(self.application_id + ':5m', expiration_time=300)

    @cached_property
    def webassets_path(self):
        return utils.module_path('onegov.election_day', 'assets')

    @cached_property
    def webassets_bundles(self):

        jsminifier = 'rjsmin'

        common = Bundle(
            'js/modernizr.js',
            'js/jquery.js',
            'js/fastclick.js',
            'js/foundation.js',
            'js/underscore.js',
            'js/stackable.js',
            'js/common.js',
            filters=jsminifier,
            output='bundles/common.bundle.js'
        )

        form_js = Bundle(
            'js/jquery.datetimepicker.js',
            'js/datetimepicker.js',
            asset('js/form_dependencies.js'),
            filters=jsminifier,
            output='bundles/jquery.datetimepicker.bundle.js'
        )

        form_css = Bundle(
            'css/jquery.datetimepicker.css',
            filters='cssmin',
            output='bundles/jquery.datetimepicker.bundle.css'
        )

        ballot_map = Bundle(
            'js/d3.js',
            'js/d3tip.js',
            'js/topojson.js',
            'js/ballot-map.js',
            filters=jsminifier,
            output='bundles/d3.bundle.js'
        )

        return {
            'common': common,
            'ballot_map': ballot_map,
            'form_js': form_js,
            'form_css': form_css,
        }


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


@ElectionDayApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@ElectionDayApp.tween_factory(over=transaction_tween_factory)
def micro_cache_anonymous_pages_tween_factory(app, handler):

    cache_paths = (
        '/',
        '/ballot/.*',
        '/vote/.*',
        '/votes/.*',
    )

    cache_paths = re.compile(r'^({})$'.format('|'.join(cache_paths)))

    def micro_cache_anonymous_pages_tween(request):
        """ Set the current language on the session manager for each request,
        for translatable database columns.

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

        # each page is cached once per language (and by application id as the
        # pages_cache is bound to it)
        key = ':'.join((request.locale, request.path_info))

        return app.pages_cache.get_or_create(key, lambda: handler(request))

    return micro_cache_anonymous_pages_tween
