from onegov.core import Framework, utils
from onegov.file import DepotApp
from onegov.onboarding.theme import OnboardingTheme
from onegov.reservation import LibresIntegration
from onegov.search import ElasticsearchApp


class OnboardingApp(Framework, LibresIntegration, DepotApp, ElasticsearchApp):

    serve_static_files = True

    def configure_onboarding(self, **cfg):
        self.onboarding = cfg['onboarding']
        assert 'onegov.town' in self.onboarding
        assert 'namespace' in self.onboarding['onegov.town']


@OnboardingApp.static_directory()
def get_static_directory():
    return 'static'


@OnboardingApp.template_directory()
def get_template_directory():
    return 'templates'


@OnboardingApp.setting(section='core', name='theme')
def get_theme():
    return OnboardingTheme()


@OnboardingApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.onboarding', 'locale'),
        utils.module_path('onegov.town', 'locale'),
        utils.module_path('onegov.org', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@OnboardingApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH'}


@OnboardingApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@OnboardingApp.webasset_path()
def get_js_path():
    return 'assets/js'


@OnboardingApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@OnboardingApp.webasset('common')
def get_common_asset():
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'placeholder.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'colorpicker.js'
    yield 'awesomeplete.js'
    yield 'common.js'
