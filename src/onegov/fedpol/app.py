from __future__ import annotations

from onegov.core import utils
from onegov.fedpol.initial_content import create_new_organisation
from onegov.fedpol.request import FedpolRequest
from onegov.fedpol.theme import FedpolTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_common_asset as default_common_asset
from onegov.town6.app import get_i18n_localedirs as get_town6_i18n_localedirs


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.org.models import Organisation


class FedpolApp(TownApp):

    localizeable = True
    request_class = FedpolRequest


@FedpolApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@FedpolApp.setting(section='core', name='theme')
def get_theme() -> FedpolTheme:
    return FedpolTheme()


@FedpolApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[FedpolApp, str], Organisation]:
    return create_new_organisation


@FedpolApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = utils.module_path('onegov.fedpol', 'locale')
    return [mine, *get_town6_i18n_localedirs()]


@FedpolApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH', 'fr_CH', 'it_CH'}


@FedpolApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@FedpolApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@FedpolApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@FedpolApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield from default_common_asset()
    yield 'fedpol.js'
