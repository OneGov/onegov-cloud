from cached_property import cached_property
from hipchat import HipChat
from onegov.core import Framework, utils
from onegov.libres import LibresIntegration
from onegov.onboarding import log
from onegov.onboarding.theme import OnboardingTheme
from webassets import Bundle


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

    @cached_property
    def webassets_path(self):
        return utils.module_path('onegov.onboarding', 'assets')

    @cached_property
    def webassets_bundles(self):

        jsminifier = None

        common = Bundle(
            'js/modernizr.js',
            'js/jquery.js',
            'js/placeholder.js',
            'js/fastclick.js',
            'js/foundation.js',
            'js/underscore.js',
            'js/colorpicker.js',
            'js/awesomeplete.js',
            'js/common.js',
            filters=jsminifier,
            output='bundles/common.bundle.js'
        )

        return {
            'common': common
        }


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
