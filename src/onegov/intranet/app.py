from __future__ import annotations

from onegov.town6 import TownApp
from typing import Any
from typing import TYPE_CHECKING
from onegov.town6.custom import get_global_tools


if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


class IntranetApp(TownApp):

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = True,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:

        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg
        )


@IntranetApp.template_variables()
def get_template_variables(request: TownRequest) -> RenderData:
    return {
        'global_tools': tuple(get_global_tools(request)),
        'hide_search_header': not request.is_logged_in
    }


# NOTE: Intranet doesn't need a citizen login
@IntranetApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False
