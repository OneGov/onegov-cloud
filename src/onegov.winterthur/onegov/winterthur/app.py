import re

from cached_property import cached_property
from onegov.core import utils
from onegov.core.static import StaticFile
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as default_common_asset
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.winterthur.initial_content import create_new_organisation
from onegov.winterthur.roadwork import RoadworkClient
from onegov.winterthur.roadwork import RoadworkConfig
from onegov.winterthur.theme import WinterthurTheme


class WinterthurApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '0.7.2'

    serve_static_files = True

    frame_ancestors = {
        'https://winterthur.ch',
        'https://*.winterthur.ch',
        'http://localhost:8000',
    }

    # disable same site cookie protection as we need to run inside iframes
    # with cookies enabled
    same_site_cookie_policy = None

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)

    def enable_iframes(self, request):
        request.content_security_policy.frame_ancestors |= self.frame_ancestors
        request.include('iframe-resizer')

    @property
    def roadwork_cache(self):
        # the expiration time is high here, as the expiration is more closely
        # managed by the roadwork client
        return self.get_cache('roadwork', expiration_time=60 * 60 * 24)

    @cached_property
    def roadwork_client(self):
        config = RoadworkConfig.lookup()

        return RoadworkClient(
            cache=self.roadwork_cache,
            hostname=config.hostname,
            endpoint=config.endpoint,
            username=config.username,
            password=config.password
        )

    def static_file(self, path):
        return StaticFile(path, version=self.version)


@WinterthurApp.tween_factory()
def enable_iframes_tween_factory(app, handler):
    iframe_paths = (
        r'/streets.*',
        r'/director(y|ies|y-submission/.*)',
        r'/ticket/.*',
        r'/mission-report.*',
        r'/roadwork.*',
        r'/daycare-subsidy-calculator',
    )

    iframe_paths = re.compile(rf"({'|'.join(iframe_paths)})")

    def enable_iframes_tween(request):
        """ Enables iframes on matching paths. """

        result = handler(request)

        if iframe_paths.match(request.path_info):
            request.app.enable_iframes(request)

        return result

    return enable_iframes_tween


@WinterthurApp.template_directory()
def get_template_directory():
    return 'templates'


@OrgApp.static_directory()
def get_static_directory():
    return 'static'


@WinterthurApp.setting(section='core', name='theme')
def get_theme():
    return WinterthurTheme()


@WinterthurApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@WinterthurApp.setting(section='org', name='default_directory_search_widget')
def get_default_directory_search_widget():
    return 'inline'


@WinterthurApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.winterthur', 'locale')
    return [mine] + get_org_i18n_localedirs()


@WinterthurApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WinterthurApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@WinterthurApp.webasset('street-search')
def get_search_asset():
    yield 'wade.js'
    yield 'string-score.js'
    yield 'street-search.js'


@WinterthurApp.webasset('iframe-resizer')
def get_iframe_resizer():
    yield 'iframe-resizer-options.js'
    yield 'iframe-resizer-contentwindow.js'


@WinterthurApp.webasset('iframe-enhancements')
def get_iframe_enhancements():
    yield 'iframe-enhancements.js'


@WinterthurApp.webasset('common')
def get_common_asset():
    yield from default_common_asset()
    yield 'winterthur.js'
