from __future__ import annotations

import re
from datetime import timedelta
from functools import cached_property

from sedate import utcnow
from typing import TYPE_CHECKING

from onegov.org import OrgApp
from onegov.org.layout import DefaultLayout
from onegov.org.models import Boardlet, BoardletFact, News
from onegov.page import Page
from onegov.plausible.plausible_api import PlausibleAPI
from onegov.ticket import Ticket
from onegov.town6 import _

if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Session

    from onegov.org.request import OrgRequest
    from onegov.town6.request import TownRequest


class OrgBoardlet(Boardlet):

    request: OrgRequest

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

        return None


@OrgApp.boardlet(name='ticket', order=(1, 1), icon='fa-ticket-alt')
class TicketBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Tickets')

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

        closed_tickets_count = (
            self.session.query(Ticket).
            filter(Ticket.closed_on.isnot(None)).
            filter(Ticket.closed_on >= time_30d_ago).count())
        yield BoardletFact(
            text=_('Closed Tickets in the Last Month'),
            number=closed_tickets_count,
            icon='fa-check-circle'
        )

        query = (
            self.session.query(Ticket).
            filter(Ticket.closed_on.isnot(None)).
            filter(Ticket.closed_on >= time_30d_ago))
        closed_tickets_count = query.count()
        closed_tickets = query.all()

        # average lead time from opening to closing
        average_lead_time_s: float | None = None
        if closed_tickets:
            total_lead_time_s = sum(
                (t.reaction_time or 0) + (t.process_time or 0)
                for t in closed_tickets)
            average_lead_time_s = total_lead_time_s / closed_tickets_count
            average_lead_time_s = round(average_lead_time_s / 86400, 1)

        yield BoardletFact(
            text=_('Lead Time from opening to closing in Days '
                   'over the Last Month'),
            number=average_lead_time_s or '-',
            icon='fa-clock'
        )

        # average lead time from pending to closing
        average_lead_time_s = None
        if closed_tickets:
            total_lead_time_s = sum(t.process_time for t in closed_tickets)
            average_lead_time_s = total_lead_time_s / len(closed_tickets)
            average_lead_time_s = round(average_lead_time_s / 86400, 1)

        yield BoardletFact(
            text=_('Lead Time from pending to closing in Days '
                   'over the Last Month'),
            number=average_lead_time_s or '-',
            icon='fa-clock'
        )


def get_icon_for_access_level(access: str) -> str:
    access_icons = {
        'public': 'fa-eye',
        'secret': 'fa-user-secret',
        'private': 'fa-lock',
        'member': 'fa-users'
    }

    if access not in access_icons:
        raise ValueError(f'Invalid access: {access}')

    return access_icons[access]


def get_icon_title(request: OrgRequest, access: str) -> str:
    access_texts = {
        'public': 'Public',
        'secret': 'Through URL only (not listed)',
        'private': 'Only by privileged users',
        'member': 'Only by privileged users and members'
    }
    if access not in ['public', 'secret', 'private', 'member']:
        raise ValueError(f'Invalid access: {access}')

    a = request.translate(_('Access'))
    b = request.translate(_(access_texts[access]))
    return f'{a}: {b}'


@OrgApp.boardlet(name='pages', order=(1, 2), icon='fa-edit')
class EditedPagesBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Last Edited Pages')

    @property
    def facts(self) -> Iterator[BoardletFact]:

        last_edited_pages = self.session.query(Page).order_by(
            Page.last_change.desc()).limit(8)

        for p in last_edited_pages:
            yield BoardletFact(
                text='',
                link=(self.layout.request.link(p), p.title),
                icon=get_icon_for_access_level(p.access),  # type:ignore[attr-defined]
                icon_title=get_icon_title(self.request, p.access)  # type:ignore[attr-defined]
            )


@OrgApp.boardlet(name='news', order=(1, 3), icon='fa-edit')
class EditedNewsBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Last Edited News')

    @property
    def facts(self) -> Iterator[BoardletFact]:
        last_edited_news = self.session.query(News).order_by(
            Page.last_change.desc()).limit(8)

        for n in last_edited_news:
            yield BoardletFact(
                text='',
                link=(self.layout.request.link(n), n.title),
                icon=get_icon_for_access_level(n.access),
                icon_title=get_icon_title(self.request, n.access)
            )


@OrgApp.boardlet(name='web stats', order=(2, 1))
class PlausibleStats(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Web Statistics')

    @property
    def is_available(self) -> bool:
        return self.plausible_api is not None

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.plausible_api:
            return None

        results = self.plausible_api.get_stats()
        if not results:
            yield BoardletFact(
                text=_('No data available'),
                number=None
            )

        for text, number in results.items():
            yield BoardletFact(
                text=self.request.translate(_(text)),
                number=number
            )


@OrgApp.boardlet(name='most popular pages', order=(2, 2))
class PlausibleTopPages(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Most Popular Pages')

    @property
    def is_available(self) -> bool:
        return self.plausible_api is not None

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.plausible_api:
            return None

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
