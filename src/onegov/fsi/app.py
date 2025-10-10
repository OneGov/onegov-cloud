from __future__ import annotations

from onegov.core import utils
from onegov.fsi.initial_content import create_new_organisation
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.request import FsiRequest
from onegov.fsi.theme import FsiTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_common_asset as default_common_asset
from onegov.town6.app import get_i18n_localedirs as get_town6_i18n_localedirs


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.request import CoreRequest
    from onegov.org.models import Organisation
    from onegov.user import User


class FsiApp(TownApp):

    request_class = FsiRequest

    # FSI doesn't really deal with tickets much, so no reason to send the
    # ticket statistics.
    send_ticket_statistics = False

    def fts_may_use_private_search(
        self,
        request: FsiRequest  # type:ignore[override]
    ) -> bool:
        return request.is_admin

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = False,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:
        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg
        )

    def on_login(self, request: CoreRequest, user: User) -> None:
        assert hasattr(user, 'attendee')
        if not user.attendee:
            user.attendee = CourseAttendee()


@FsiApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@TownApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@FsiApp.setting(section='core', name='theme')
def get_theme() -> FsiTheme:
    return FsiTheme()


@FsiApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[FsiApp, str], Organisation]:
    return create_new_organisation


# NOTE: Fsi doesn't need a citizen login
@FsiApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False


@FsiApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = utils.module_path('onegov.fsi', 'locale')
    return [mine, *get_town6_i18n_localedirs()]


@FsiApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@FsiApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@FsiApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield from default_common_asset()
    yield 'fsi.js'
