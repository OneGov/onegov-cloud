from __future__ import annotations

from babel import Locale
from decimal import Decimal
from decimal import ROUND_HALF_UP
from functools import cached_property
from markupsafe import Markup
from numbers import Integral
from numbers import Number
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.models import TranslatablePageMove
from onegov.user import Auth


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.app import SwissvotesApp
    from onegov.swissvotes.models import SwissVote
    from onegov.swissvotes.request import SwissvotesRequest


class DefaultLayout(ChameleonLayout):

    app: SwissvotesApp
    request: SwissvotesRequest

    day_long_format = 'skeleton:MMMMd'
    date_long_format = 'long'
    datetime_long_format = 'medium'

    def __init__(self, model: Any, request: SwissvotesRequest) -> None:
        super().__init__(model, request)
        self.request.include('frameworks')
        self.request.include('chosen')
        self.request.include('common')
        if 'swissvotes.ch' in request.url:
            self.request.include('stats')

        self.pages = TranslatablePageCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return ''

    @cached_property
    def top_navigation(self) -> list[Link]:
        result = [
            Link(
                page.title,
                self.request.link(page),
                sortable_id=page.id,
            )
            for page in self.pages.query()
            if page.id not in self.request.app.static_content_pages
        ]
        result.insert(0, Link(_('Votes'), self.votes_url))
        return result

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [Link(_('Homepage'), self.homepage_url)]

    @cached_property
    def static_path(self) -> str:
        return self.request.link(self.app.principal, 'static')

    @cached_property
    def sentry_init_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    @cached_property
    def homepage_url(self) -> str:
        return self.request.link(self.app.principal)

    @cached_property
    def disclaimer_link(self) -> Link:
        page = self.pages.setdefault('disclaimer')
        return Link(page.title, self.request.link(page))

    @cached_property
    def imprint_link(self) -> Link:
        page = self.pages.setdefault('imprint')
        return Link(page.title, self.request.link(page))

    @cached_property
    def data_protection_link(self) -> Link:
        page = self.pages.setdefault('data-protection')
        return Link(page.title, self.request.link(page))

    @cached_property
    def votes_url(self) -> str:
        return self.request.link(SwissVoteCollection(self.request.app))

    @cached_property
    def login_url(self) -> str | None:
        if not self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_url),
                name='login'
            )
        return None

    @cached_property
    def logout_url(self) -> str | None:
        if self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_url),
                name='logout'
            )
        return None

    @cached_property
    def move_page_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                TranslatablePageMove,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )

    @cached_property
    def locales(self) -> list[tuple[str, str, str, str]]:
        result = []
        assert self.app.locales == {'de_CH', 'fr_CH', 'en_US'}
        for locale_code in ('de_CH', 'fr_CH', 'en_US'):
            locale = Locale.parse(locale_code)
            language_name = locale.get_language_name() or locale.language
            result.append((
                locale_code,
                locale.language,
                language_name.capitalize(),
                SiteLocale(locale_code).link(self.request, self.request.url)
            ))
        return result

    def format_policy_areas(self, vote: SwissVote) -> Markup:
        paths: dict[str, list[list[str]]] = {}
        for path in (area.label_path for area in vote.policy_areas):
            paths.setdefault(path[0], []).append(path)

        translate = self.request.translate
        return Markup(',<br>').join(
            Markup('<span title="{}">{}</span>').format(
                Markup(' &#10;&#10;').join(
                    Markup(' &gt; ').join(translate(part) for part in title)
                    for title in titles
                ),
                translate(value)
            )
            for value, titles in paths.items()
        )

    def format_bfs_number(
        self,
        number: Decimal
    ) -> str:
        """ Hide the decimal places if there are none (simple votes). """

        decimal_places = 0 if number.to_integral_value() == number else 1
        return self.format_number(number, decimal_places)

    def format_number(
        self,
        number: Number | Decimal | float | str | None,
        decimal_places: int | None = None,
        padding: str = ''
    ) -> str:
        """ Takes the given numer and formats it according to locale.

        If the number is an integer, the default decimal places are 0,
        otherwise 2.

        Overwrites parent class to use "." instead of "," for fr_CH locale
        as would be returned by babel.

        """
        if number is None:
            return ''

        if decimal_places is None:
            if isinstance(number, Integral):
                decimal_places = 0
            else:
                decimal_places = 2

        number = Decimal(number).quantize(  # type:ignore[arg-type]
            Decimal(10) ** -decimal_places,
            rounding=ROUND_HALF_UP
        )

        locale = self.request.locale
        # Fixes using "," for french locale instead of "." as for german
        if locale == 'fr_CH':
            locale = 'de_CH'
        decimal, group = self.request.number_symbols(locale)
        result = '{{:{},.{}f}}'.format(padding, decimal_places).format(number)
        return result.translate({ord(','): group, ord('.'): decimal})
