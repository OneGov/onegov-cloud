from onegov.core import utils
from onegov.org import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.winterthur.initial_content import create_new_organisation
from onegov.winterthur.theme import WinterthurTheme


class WinterthurApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '0.1.8'

    frame_ancestors = {
        'https://winterthur.ch',
        'https://*.winterthur.ch'
    }

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)

    def enable_iframes(self, request):
        request.content_security_policy.frame_ancestors |= self.frame_ancestors


@WinterthurApp.template_directory()
def get_template_directory():
    return 'templates'


@WinterthurApp.setting(section='core', name='theme')
def get_theme():
    return WinterthurTheme()


@WinterthurApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@WinterthurApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.winterthur', 'locale')
    return [mine] + get_org_i18n_localedirs()


@WinterthurApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WinterthurApp.webasset('street-search')
def get_search_asset():
    yield 'wade.js'
    yield 'string-score.js'
    yield 'street-search.js'


@WinterthurApp.webasset('iframe-resizer')
def get_iframe_resizer():
    yield 'iframe-resizer-options.js'
    yield 'iframe-resizer-contentwindow.js'
