from __future__ import annotations

from functools import cached_property
from onegov.core.utils import module_path
from onegov.pas.content import create_new_organisation
from onegov.pas.custom import get_global_tools
from onegov.pas.custom import get_top_navigation
from onegov.pas.request import PasRequest
from onegov.pas.theme import PasTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_i18n_localedirs as get_i18n_localedirs_base


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.types import RenderData
    from onegov.org.models import Organisation
    from onegov.town6.request import TownRequest


class PasApp(TownApp):
    request_class = PasRequest


@PasApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[TownApp, str], Organisation]:
    return create_new_organisation


# NOTE: PAS doesn't need a citizen login
@PasApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False


@PasApp.template_variables()
def get_template_variables(request: TownRequest) -> RenderData:
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
    }


@PasApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@PasApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


# @PasApp.webasset_path()
# def get_js_path() -> str:
#     return 'assets/js'


@PasApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = module_path('onegov.pas', 'locale')
    return [mine, *get_i18n_localedirs_base()]


@PasApp.setting(section='core', name='theme')
def get_theme() -> PasTheme:
    return PasTheme()
