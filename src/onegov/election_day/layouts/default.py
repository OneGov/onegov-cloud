from __future__ import annotations

from babel import Locale
from fs.errors import ResourceNotFound
from functools import cached_property
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.election_day import _
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.collections import VoteCollection
from onegov.user import Auth
from sedate import utcnow


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.election_day.app import ElectionDayApp
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.request import ElectionDayRequest
    from typing import Protocol

    class HasName(Protocol):
        @property
        def name(self) -> str: ...


class DefaultLayout(ChameleonLayout):

    day_long_format = 'skeleton:MMMMd'
    date_long_format = 'long'
    datetime_long_format = 'medium'

    docs_base_url = ('https://github.com/OneGov/onegov-cloud/blob/master/src'
                     '/onegov/election_day/static/docs/api')

    app: ElectionDayApp
    request: ElectionDayRequest

    def __init__(self, model: Any, request: ElectionDayRequest) -> None:
        super().__init__(model, request)

        self.request.include('common')
        self.request.include('chosen')
        self.request.include('custom')

        if 'headerless' in request.params:
            request.browser_session['headerless'] = True
        if 'headerful' in request.params:
            if request.browser_session.has('headerless'):
                del request.browser_session['headerless']

    def title(self) -> str:
        return ''

    @cached_property
    def principal(self) -> Canton | Municipality:
        return self.request.app.principal

    def label(self, value: str) -> str:
        return self.principal.label(value)

    @cached_property
    def has_districts(self) -> bool:
        if (
            self.principal.domain == 'canton'
            and getattr(self.model, 'domain', None) == 'municipality'
        ):
            return False
        return self.principal.has_districts

    @cached_property
    def has_regions(self) -> bool:
        return self.principal.has_regions

    @cached_property
    def has_superregions(self) -> bool:
        return False

    @cached_property
    def homepage_link(self) -> str:
        return self.request.link(self.principal)

    def get_opendata_link(self, lang: str) -> str:
        return f'{self.docs_base_url}/open_data_{lang}.md'

    @cached_property
    def opendata_link(self) -> str:
        lang = (self.request.locale or 'en')[:2]
        return self.get_opendata_link(lang)

    @cached_property
    def terms_icon(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'images/terms_by.svg'
        )

        return self.request.link(static_file)

    @cached_property
    def terms_link(self) -> str:
        lang = (self.request.locale or 'en')[:2]
        return f'https://opendata.swiss/{lang}/terms-of-use'

    @cached_property
    def format_description_link(self) -> str:
        lang = (self.request.locale or 'en')[:2]
        return f'{self.docs_base_url}/format__{lang}.md'

    @cached_property
    def font_awesome_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css')

        return self.request.link(static_file)

    @cached_property
    def sentry_init_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    def get_topojson_link(self, id: str, year: int) -> str:
        return self.request.link(
            StaticFile(f'mapdata/{year}/{id}.json')
        )

    @cached_property
    def copyright_year(self) -> int:
        return utcnow().year

    @cached_property
    def manage_link(self) -> str:
        return self.request.link(VoteCollection(self.app.session()))

    @cached_property
    def login_link(self) -> str | None:
        if not self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.manage_link),
                name='login'
            )
        return None

    @cached_property
    def logout_link(self) -> str | None:
        if self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request), name='logout')
        return None

    @cached_property
    def archive(self) -> ArchivedResultCollection:
        return ArchivedResultCollection(self.request.session)

    @cached_property
    def archive_search_link(self) -> str:
        return self.request.class_link(
            SearchableArchivedResultCollection,
            variables={'item_type': 'vote'}
        )

    @cached_property
    def locales(self) -> list[tuple[str, str]]:
        to = self.request.url

        def get_name(locale: str) -> str:
            name = Locale.parse(locale).get_language_name()
            if name is None:
                name = locale
            return name.capitalize()

        def get_link(locale: str) -> str:
            return SiteLocale(locale).link(self.request, to)

        return [
            (get_name(locale), get_link(locale))
            for locale in sorted(self.app.locales)
        ]

    def format_name(self, item: HasName) -> str:
        if hasattr(item, 'entity_id'):
            return item.name if item.entity_id else _('Expats')
        return item.name or _('Expats')

    @cached_property
    def logo_alt_text(self) -> str:
        alt_text = (
            f'Logo: '
            f'{self.principal.name} '
            f'{self.request.translate(_("Link to homepage"))}'
        )
        return alt_text

    @cached_property
    def archive_download(self) -> str:
        return self.request.link(self.principal, name='archive-download')

    @property
    def last_archive_modification(self) -> datetime | None:
        try:
            filestorage = self.request.app.filestorage
            assert filestorage is not None
            filestorage_info = filestorage.getinfo(
                'archive/zip/archive.zip', namespaces='details'
            )
            return filestorage_info.modified
        except ResourceNotFound:
            pass
        return None
