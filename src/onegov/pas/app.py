from __future__ import annotations

import logging

from onegov.core.utils import module_path
from onegov.org.models import Organisation
from onegov.pas.content import create_new_organisation
from onegov.pas.custom import get_global_tools
from onegov.pas.custom import get_top_navigation
from onegov.pas.models import PASParliamentarian
from onegov.pas.request import PasRequest
from onegov.pas.theme import PasTheme
from onegov.town6 import TownApp
from onegov.town6.app import get_i18n_localedirs as get_i18n_localedirs_base
from purl import URL


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.types import RenderData
    from morepath.authentication import NoIdentity
    from morepath.authentication import Identity
    from onegov.user import User
    from onegov.user.integration import EnsureUserCallback

log = logging.getLogger('onegov.pas')


class PasApp(TownApp):
    request_class = PasRequest

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = False,
        disable_password_reset: bool = False,
        **cfg: Any,
    ) -> None:
        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg,
        )

    def configure_kub_api(
        self,
        *,
        kub_api_token: str = '',
        kub_base_url: str = '',
        kub_cert_dir: str = '',
        **cfg: Any
    ) -> None:
        """Configure KUB API settings for data import."""
        self.kub_api_token = kub_api_token
        self.kub_base_url = kub_base_url
        self.kub_cert_dir = kub_cert_dir

    def redirect_after_login(
        self,
        identity: Identity | NoIdentity,
        request: PasRequest,  # type:ignore[override]
        default: str
    ) -> str | None:

        if default != '/' and '/auth/login' not in str(default):
            return None
        return URL(request.class_link(Organisation)).path()


@PasApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[TownApp, str], Organisation]:
    return create_new_organisation


# NOTE: PAS doesn't need a citizen login
@PasApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False


@PasApp.template_variables()
def get_template_variables(request: PasRequest) -> RenderData:
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


@PasApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@PasApp.webasset('custom')
def get_custom_webasset() -> Iterator[str]:
    yield 'custom.js'


@PasApp.webasset('importlog')
def get_logfilter_webasset() -> Iterator[str]:
    yield 'importlog.js'


@PasApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = module_path('onegov.pas', 'locale')
    return [mine, *get_i18n_localedirs_base()]


@PasApp.setting(section='core', name='theme')
def get_theme() -> PasTheme:
    return PasTheme()


@PasApp.setting(section='user', name='ensure_user_callback')
def get_ensure_user_callback() -> EnsureUserCallback:

    def on_ensure_user(
        user: User | None,
        request: Any,
        /,
        *,
        source: str | None,
        source_id: str | None,
        username: str,
        role: str,
        realname: str | None,
        force_role: bool,
        force_active: bool,
    ) -> User | Literal[True] | None:
        log.info(
            f'SAML2 on_ensure_user: username={username!r}, '
            f'source={source!r}, source_id={source_id!r}, '
            f'role={role!r}, realname={realname!r}, '
            f'user_found={user is not None}'
        )

        if role != 'member':
            return True

        if not user and source_id:
            session = request.session
            parliamentarian = (
                session.query(PASParliamentarian)
                .filter_by(zg_username=source_id)
                .first()
            )
            if parliamentarian:
                user = parliamentarian.user
        if not user:
            log.info(
                f'SAML2: no user for username={username!r} '
                f'source_id={source_id!r}'
            )
            return None

        # The `hourly_kub_data_import` has run in the background created users
        # for parliamentarians and set these roles via
        # `PasParliamentarianCollection.sync_user_accounts()`.
        parliamentarian_roles = {'parliamentarian', 'commission_president'}
        if user.role not in parliamentarian_roles:
            log.info(
                f'SAML2: user {username} has unexpected role '
                f'{user.role!r} for member SSO login'
            )
            return None

        if not user.active:
            user.active = True

        if user.source != source:
            user.source = source
        if user.source_id != source_id:
            user.source_id = source_id
        return user

    return on_ensure_user
