from __future__ import annotations

from onegov.core import utils
from onegov.core.i18n import default_locale_negotiator
from onegov.ilz.initial_content import create_new_organisation
from onegov.ilz.request import ILZRequest
from onegov.ilz.theme import ILZTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_common_asset as default_common_asset
from onegov.town6.app import get_i18n_localedirs as get_town6_i18n_localedirs


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from onegov.org.models import Organisation


class ILZApp(TownApp):

    localizeable = True
    request_class = ILZRequest  # type: ignore[assignment]


@ILZApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@ILZApp.setting(section='core', name='theme')
def get_theme() -> ILZTheme:
    return ILZTheme()


@ILZApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[ILZApp, str], Organisation]:
    return create_new_organisation


@ILZApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = utils.module_path('onegov.ilz', 'locale')
    return [mine, *get_town6_i18n_localedirs()]


@ILZApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH', 'fr_CH', 'it_CH'}


@ILZApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@ILZApp.setting(section='i18n', name='locale_negotiator')
def get_locale_negotiator(
) -> Callable[[Sequence[str], ILZRequest], str | None]:
    return default_locale_negotiator


@ILZApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@ILZApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@ILZApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield from default_common_asset()
    yield 'ilz.js'
