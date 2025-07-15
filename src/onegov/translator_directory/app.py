from __future__ import annotations

from functools import cached_property
from onegov.core import utils
from onegov.gis import Coordinates
from onegov.translator_directory.initial_content import create_new_organisation
from onegov.town6 import TownApp
from onegov.town6.app import get_common_asset as default_common_asset
from onegov.town6.app import get_i18n_localedirs as get_town_i18n_localedirs
from onegov.org.models import Organisation, GeneralFile, GeneralFileCollection
from onegov.translator_directory.request import TranslatorAppRequest
from onegov.translator_directory.theme import TranslatorDirectoryTheme
from purl import URL
from sqlalchemy import and_


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from morepath.authentication import Identity, NoIdentity
    from onegov.gis.models.coordinates import AnyCoordinates


class TranslatorDirectoryApp(TownApp):

    send_ticket_statistics = False
    request_class = TranslatorAppRequest

    def es_may_use_private_search(
        self,
        request: TranslatorAppRequest  # type:ignore[override]
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

    @property
    def coordinates(self) -> AnyCoordinates:
        return self.org.meta.get('translator_directory_home') or Coordinates()

    @coordinates.setter
    def coordinates(self, value: AnyCoordinates) -> None:
        self.org.meta['translator_directory_home'] = value or {}

    def redirect_after_login(
        self,
        identity: Identity | NoIdentity,
        request: TranslatorAppRequest,  # type:ignore[override]
        default: str
    ) -> str | None:

        if default != '/' and '/auth/login' not in str(default):
            return None
        return URL(request.class_link(Organisation)).path()

    # We deliberately do not use @orm_cached here, because if the user
    # uploads a new file, it's not immediately visible in the list of
    # available templates.
    @property
    def mail_templates(self) -> list[str]:
        """ Templates are special docx files which are filled with
        variables. These files are manually uploaded. """
        query = GeneralFileCollection(self.session()).query().filter(
            and_(
                GeneralFile.name.like('Vorlage%'),
                GeneralFile.name.like('%.docx')
            )
        ).with_entities(GeneralFile.name)
        return [filename for filename, in query]

    @cached_property
    def mailto_link(self) -> str:
        from onegov.translator_directory.models.translator import Translator
        q = self.session().query(Translator).with_entities(
            Translator.email)
        emails = q.distinct().all()
        bcc_addresses = '; '.join(str(email) for (email,) in emails if email)
        mailto_link = f'mailto:?bcc={bcc_addresses}'
        return mailto_link


@TranslatorDirectoryApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@TranslatorDirectoryApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@TranslatorDirectoryApp.setting(section='core', name='theme')
def get_theme() -> TranslatorDirectoryTheme:
    return TranslatorDirectoryTheme()


@TranslatorDirectoryApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[TranslatorDirectoryApp, str], Organisation]:
    return create_new_organisation


# NOTE: Feriennet doesn't need a citizen login
@TranslatorDirectoryApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False


@TranslatorDirectoryApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = utils.module_path('onegov.translator_directory', 'locale')
    return [mine, *get_town_i18n_localedirs()]


@TranslatorDirectoryApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@TranslatorDirectoryApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@TranslatorDirectoryApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield from default_common_asset()
    yield 'translator_directory.js'
