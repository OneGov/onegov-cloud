from __future__ import annotations

import re
from datetime import timedelta
from functools import cached_property

from sedate import utcnow
from typing import TYPE_CHECKING

from onegov.org.layout import DefaultLayout
from onegov.org.models import Boardlet, BoardletFact, News
from onegov.page import Page
from onegov.plausible.plausible_api import PlausibleAPI
from onegov.ticket import Ticket
from onegov.town6 import TownApp, _

if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Session

    from onegov.town6.request import TownRequest


class TownBoardlet(Boardlet):

    request: TownRequest

    @cached_property
    def session(self) -> Session:
        return self.request.session

    @cached_property
    def layout(self) -> DefaultLayout:
        return DefaultLayout(None, self.request)

    @cached_property
    def plausible_api(self) -> PlausibleAPI:
        site_id = None
        analytics_code = self.request.app.org.analytics_code

        if analytics_code:
            if 'analytics.seantis.ch' in analytics_code:
                match = re.search(r'data-domain="(.+?)"', analytics_code)
                site_id = match.group(1) if match else None

        return PlausibleAPI(site_id)


@TownApp.boardlet(name='ticket', order=(1, 1), icon='fa-ticket-alt')
class TicketBoardlet(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Tickets'

    @property
    def facts(self) -> Iterator[BoardletFact]:

        yield BoardletFact(
            text=_('Open Tickets'),
            number=self.session.query(Ticket).filter_by(state='open').count(),
            icon='fa-hourglass'
        )

        yield BoardletFact(
            text=_('Pending Tickets'),
            number=self.session.query(Ticket).filter_by(
                state='pending').count(),
            icon='fa-hourglass-half'
        )

        time_30d_ago = utcnow() - timedelta(days=30)

        new_tickets = self.session.query(Ticket).filter(
            Ticket.created > time_30d_ago).count()
        yield BoardletFact(
            text=_('New Tickets in the Last Month'),
            number=new_tickets,
            icon='fa-plus-circle'
        )

        closed_tickets = (
            self.session.query(Ticket).
            filter(Ticket.closed_on.isnot(None)).
            filter(Ticket.closed_on >= time_30d_ago).count())
        yield BoardletFact(
            text=_('Closed Tickets in the Last Month'),
            number=closed_tickets,
            icon='fa-check-circle'
        )

        closed_tickets = (
            self.session.query(Ticket).
            filter(Ticket.closed_on.isnot(None)).
            filter(Ticket.closed_on >= time_30d_ago).all())

        # average lead time from opening to closing
        average_lead_time_s: float | str = '-'
        if closed_tickets:
            total_lead_time_s = sum(
                t.reaction_time + t.process_time for t in closed_tickets)
            average_lead_time_s = total_lead_time_s / len(closed_tickets)
            average_lead_time_s = round(average_lead_time_s / 86400, 1)

        yield BoardletFact(
            text=_('Lead Time from opening to closing in Days '
                   'over the Last Month '),
            number=average_lead_time_s,
            icon='fa-clock'
        )

        # average lead time from pending to closing
        average_lead_time_s = '-'
        if closed_tickets:
            total_lead_time_s = sum(t.process_time for t in closed_tickets)
            average_lead_time_s = total_lead_time_s / len(closed_tickets)
            average_lead_time_s = round(average_lead_time_s / 86400, 1)

        yield BoardletFact(
            text=_('Lead Time from pending to closing in Days '
                   'over the Last Month'),
            number=average_lead_time_s,
            icon='fa-clock'
        )


def get_icon_for_visibility(visibility: str) -> str:
    visibility_icons = {
        'public': 'fa-eye',
        'secret': 'fa-user-secret',
        'private': 'fa-lock',
        'member': 'fa-users'
    }

    if visibility not in visibility_icons:
        raise ValueError(f'Invalid visibility: {visibility}')

    return visibility_icons[visibility]


def get_icon_title(request: TownRequest, visibility: str) -> str:
    if visibility not in ['public', 'secret', 'private', 'member']:
        raise ValueError(f'Invalid visibility: {visibility}')

    return request.translate(_('Visibility ${visibility}',
                             mapping={'visibility': visibility}))


@TownApp.boardlet(name='pages', order=(1, 2), icon='fa-edit')
class EditedPagesBoardlet(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Last Edited Pages'

    @property
    def facts(self) -> Iterator[BoardletFact]:

        last_edited_pages = self.session.query(Page).order_by(
            Page.last_change.desc()).limit(8)

        for p in last_edited_pages:
            yield BoardletFact(
                text='',
                link=(self.layout.request.link(p), p.title),
                icon=get_icon_for_visibility(p.access),  # type:ignore[attr-defined]
                icon_title=get_icon_title(self.request, p.access)  # type:ignore[attr-defined]
            )


@TownApp.boardlet(name='news', order=(1, 3), icon='fa-edit')
class EditedNewsBoardlet(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Last Edited News'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        last_edited_news = self.session.query(News).order_by(
            Page.last_change.desc()).limit(8)

        for n in last_edited_news:
            yield BoardletFact(
                text='',
                link=(self.layout.request.link(n), n.title),
                icon=get_icon_for_visibility(n.access),
                icon_title=get_icon_title(self.request, n.access)
            )


@TownApp.boardlet(name='web-stats', order=(2, 1))
class PlausibleStats(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Web Statistics'

    @property
    def enabled(self) -> bool:
        return self.plausible_api.site_id is not None

    @property
    def facts(self) -> Iterator[BoardletFact]:

        results = self.plausible_api.get_stats()
        if not results:
            yield BoardletFact(
                text=_('No data available'),
                number=None
            )

        for text, number in results.items():
            yield BoardletFact(
                text=text,
                number=number
            )


@TownApp.boardlet(name='Top Pages', order=(2, 2))
class PlausibleTopPages(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Top Pages'

    @property
    def enabled(self) -> bool:
        return self.plausible_api.site_id is not None

    @property
    def facts(self) -> Iterator[BoardletFact]:

        results = self.plausible_api.get_top_pages(limit=10)

        if not results:
            yield BoardletFact(
                text=_('No data available'),
                number=None
            )

        for text, number in results.items():
            yield BoardletFact(
                text=text,
                number=number
            )
