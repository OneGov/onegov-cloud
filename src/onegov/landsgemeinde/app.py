from onegov.core.framework import current_language_tween_factory
from onegov.core.framework import transaction_tween_factory
from onegov.core.utils import module_path
from onegov.landsgemeinde.content import create_new_organisation
from onegov.landsgemeinde.custom import get_global_tools
from onegov.landsgemeinde.custom import get_top_navigation
from onegov.landsgemeinde.theme import LandsgemeindeTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_i18n_localedirs as get_i18n_localedirs_base
from re import compile


class LandsgemeindeApp(TownApp):

    @property
    def pages_cache(self):
        """ A cache for pages. """

        return self.get_cache('pages', 300)


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


@LandsgemeindeApp.webasset_path()
def get_js_path():
    return 'assets/js'


@LandsgemeindeApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = module_path('onegov.landsgemeinde', 'locale')
    return [mine] + get_i18n_localedirs_base()


@LandsgemeindeApp.setting(section='core', name='theme')
def get_theme():
    return LandsgemeindeTheme()


@LandsgemeindeApp.webasset('ticker')
def get_backend_ticker():
    yield 'ticker.js'


@LandsgemeindeApp.webasset('person_votum')
def get_person_votum():
    yield 'person_votum.js'


@LandsgemeindeApp.webasset('agenda_items')
def get_backend_agenda_items():
    yield 'agenda_items.js'


@LandsgemeindeApp.tween_factory(
    under=current_language_tween_factory,
    over=transaction_tween_factory
)
def pages_cache_tween_factory(app, handler):

    """ Cache pages for 5 minutes. """

    cache_paths = (
        '/landsgemeinde/.*/ticker',
    )
    cache_paths = compile(r'^({})$'.format('|'.join(cache_paths)))

    def should_cache_fn(response):
        return (
            response.status_code == 200
            and 'Set-Cookie' not in response.headers
        )

    def pages_cache_tween(request):

        # do not cache POST, DELETE etc.
        if request.method not in ('GET', 'HEAD'):
            return handler(request)

        # no cache if the user is logged in
        if request.is_logged_in:
            return handler(request)

        # only cache whitelisted paths
        if not cache_paths.match(request.path_info):
            return handler(request)

        if request.method == 'HEAD':
            # HEAD requests are cached with only the path
            key = ':'.join((request.method, request.path))
        else:
            # GET requests are cached with the path and query string
            key = ':'.join((request.method, request.path_qs))

        return app.pages_cache.get_or_create(
            key,
            creator=lambda: handler(request),
            should_cache_fn=should_cache_fn
        )

    return pages_cache_tween
