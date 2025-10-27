from __future__ import annotations

from onegov.core import Framework, utils
from onegov.file import DepotApp
from onegov.onboarding.theme import OnboardingTheme
from onegov.reservation import LibresIntegration
from onegov.search import SearchApp


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


class OnboardingApp(Framework, LibresIntegration, DepotApp, SearchApp):

    serve_static_files = True

    def configure_onboarding(
        self,
        *,
        onboarding: dict[str, Any],
        **cfg: Any
    ) -> None:

        self.onboarding = onboarding
        assert 'onegov.town6' in self.onboarding
        assert 'namespace' in self.onboarding['onegov.town6']


@OnboardingApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@OnboardingApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@OnboardingApp.setting(section='core', name='theme')
def get_theme() -> OnboardingTheme:
    return OnboardingTheme()


@OnboardingApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.onboarding', 'locale'),
        utils.module_path('onegov.town6', 'locale'),
        utils.module_path('onegov.org', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@OnboardingApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH'}


@OnboardingApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@OnboardingApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@OnboardingApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@OnboardingApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'placeholder.js'
    yield 'foundation.js'
    yield 'underscore.js'
    yield 'colorpicker.js'
    yield 'awesomeplete.js'
    yield 'common.js'
