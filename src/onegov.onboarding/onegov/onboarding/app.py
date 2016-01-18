from onegov.core import Framework, utils
from onegov.libres import LibresIntegration
from onegov.onboarding.theme import OnboardingTheme


class OnboardingApp(Framework, LibresIntegration):

    serve_static_files = True

    def configure_onboarding(self, **cfg):
        self.onboarding = cfg['onboarding']
        assert 'onegov.town' in self.onboarding
        assert 'namespace' in self.onboarding['onegov.town']


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
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@OnboardingApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'
