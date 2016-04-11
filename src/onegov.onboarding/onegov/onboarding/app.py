from hipchat import HipChat
from onegov.core import Framework, utils
from onegov.libres import LibresIntegration
from onegov.onboarding import log
from onegov.onboarding.theme import OnboardingTheme


class OnboardingApp(Framework, LibresIntegration):

    serve_static_files = True

    def configure_onboarding(self, **cfg):
        self.onboarding = cfg['onboarding']
        assert 'onegov.town' in self.onboarding
        assert 'namespace' in self.onboarding['onegov.town']

    def notify_hipchat(self, message):
        if 'hipchat' in self.onboarding:
            try:
                hipchat = HipChat(token=self.onboarding['hipchat']['token'])
                hipchat.message_room(
                    room_id=self.onboarding['hipchat']['room_id'],
                    message_from='Onboarding',
                    message=message,
                    message_format='html',
                    color='green',
                    notify=True
                )
            except Exception:
                log.exception("Error during Hipchat message")


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
    yield 'fastclick.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'colorpicker.js'
    yield 'awesomeplete.js'
    yield 'common.js'
