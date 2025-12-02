from __future__ import annotations

from onegov.agency.api import AgencyApiEndpoint
from onegov.agency.api import MembershipApiEndpoint
from onegov.agency.api import PersonApiEndpoint
from onegov.agency.custom import get_global_tools
from onegov.agency.custom import get_top_navigation
from onegov.agency.forms import UserGroupForm
from onegov.agency.initial_content import create_new_organisation
from onegov.agency.pdf import AgencyPdfAr, AgencyPdfBs, AgencyPdfLu
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg
from onegov.agency.request import AgencyRequest
from onegov.agency.theme import AgencyTheme
from onegov.api import ApiApp
from onegov.core import utils
from onegov.town6 import TownApp
from onegov.town6.app import get_editor_asset as editor_assets
from onegov.town6.app import get_i18n_localedirs as get_org_i18n_localedirs


from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import SupportsRead
    from collections.abc import Callable
    from collections.abc import Iterator
    from datetime import datetime
    from fs.base import FS
    from fs.base import SubFS
    from onegov.api import ApiEndpoint
    from onegov.core.types import RenderData
    from onegov.org.models import Organisation


class AgencyApp(TownApp, ApiApp):

    request_class = AgencyRequest

    if TYPE_CHECKING:
        # FIXME: Maybe we should consider just raising an exception
        #        if filestorage is accesed without it being configured
        @property
        def filestorage(self) -> SubFS[FS]: ...

    @property
    def root_pdf_exists(self) -> bool:
        return self.filestorage.exists('root.pdf')

    @property
    def people_xlsx_exists(self) -> bool:
        return self.filestorage.exists('people.xlsx')

    @property
    def root_pdf_modified(self) -> datetime | None:
        if self.root_pdf_exists:
            return self.filestorage.getdetails('root.pdf').modified
        return None

    @property
    def people_xlsx_modified(self) -> datetime | None:
        if self.people_xlsx:
            return self.filestorage.getdetails('people.xlsx').modified
        return None

    @property
    def root_pdf(self) -> bytes | None:
        result: bytes | None = None
        if self.filestorage.exists('root.pdf'):
            with self.filestorage.open('root.pdf', 'rb') as file:
                # FS bug with mode=rb
                result = file.read()  # type:ignore[assignment]
        return result

    # FIXME: asymmetric property
    @root_pdf.setter
    def root_pdf(self, value: SupportsRead[bytes] | bytes) -> None:
        with self.filestorage.open('root.pdf', 'wb') as file:
            if hasattr(value, 'read'):
                value = value.read()
            # FS bug with mode=wb
            file.write(value)  # type:ignore

    @property
    def people_xlsx(self) -> bytes | None:
        result: bytes | None = None
        if self.filestorage.exists('people.xlsx'):
            with self.filestorage.open('people.xlsx', 'rb') as file:
                # FS bug with mode=rb
                result = file.read()  # type:ignore[assignment]
        return result

    # FIXME: asymmetric property
    @people_xlsx.setter
    def people_xlsx(self, value: SupportsRead[bytes] | bytes) -> None:
        with self.filestorage.open('people.xlsx', 'wb') as file:
            if hasattr(value, 'read'):
                value = value.read()
            # FS bug with mode=wb
            file.write(value)  # type:ignore

    @property
    def pdf_class(self) -> type[AgencyPdfDefault]:
        pdf_layout = self.org.meta.get('pdf_layout')
        if pdf_layout == 'ar':
            return AgencyPdfAr
        if pdf_layout == 'zg':
            return AgencyPdfZg
        if pdf_layout == 'bs':
            return AgencyPdfBs
        if pdf_layout == 'lu':
            return AgencyPdfLu
        return AgencyPdfDefault

    @property
    def enable_yubikey(self) -> bool:
        return self.org.meta.get('enable_yubikey', self._enable_yubikey)

    @enable_yubikey.setter
    def enable_yubikey(self, value: bool) -> None:
        self._enable_yubikey = value


@AgencyApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[AgencyApp, str], Organisation]:
    return create_new_organisation


@AgencyApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@AgencyApp.template_variables()
def get_template_variables(request: AgencyRequest) -> RenderData:
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
    }


@AgencyApp.setting(section='core', name='theme')
def get_theme() -> AgencyTheme:
    return AgencyTheme()


@AgencyApp.setting(section='org', name='usergroup_form_class')
def get_usergroup_form_class() -> type[UserGroupForm]:
    return UserGroupForm


@AgencyApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = utils.module_path('onegov.agency', 'locale')
    return [mine, *get_org_i18n_localedirs()]


@AgencyApp.setting(section='org', name='ticket_manager_roles')
def get_ticket_manager_roles() -> tuple[str, ...]:
    return ('admin', 'editor', 'member')


@AgencyApp.setting(section='org', name='disabled_extensions')
def get_disabled_extensions() -> tuple[str, ...]:
    return ('PersonLinkExtension', )


# NOTE: A citizen login doesn't make a ton of sense here, given the
#       simplicity of the tickets processed in this system, but we
#       can think about enabling it in the future.
@AgencyApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False


@AgencyApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@AgencyApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@AgencyApp.webasset('people-select')
def get_people_select_asset() -> Iterator[str]:
    yield 'people-select.js'


@AgencyApp.webasset('sortable-multi-checkbox')
def get_sortable_multi_checkbox_asset() -> Iterator[str]:
    yield 'jquery.js'
    yield 'sortable.js'
    yield 'sortable-multi-checkbox.js'


@AgencyApp.webasset('editor')
def get_editor_assets() -> Iterator[str]:
    yield from editor_assets()


@AgencyApp.setting(section='api', name='endpoints')
def get_api_endpoints_handler(
) -> Callable[[AgencyRequest], Iterator[ApiEndpoint[Any]]]:

    def get_api_endpoints(
            request: AgencyRequest,
            page: int = 0,
            extra_parameters: dict[str, Any] | None = None
    ) -> Iterator[ApiEndpoint[Any]]:
        yield AgencyApiEndpoint(request, extra_parameters, page)
        yield PersonApiEndpoint(request, extra_parameters, page)
        yield MembershipApiEndpoint(request, extra_parameters, page)

    return get_api_endpoints
