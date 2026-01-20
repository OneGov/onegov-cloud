from __future__ import annotations

from datetime import timedelta
from functools import cached_property
from sedate import utcnow
from sqlalchemy import func

from onegov.org import _
from onegov.org import OrgApp
from onegov.org.analytics import Plausible
from onegov.org.layout import DefaultLayout
from onegov.org.models import Boardlet, BoardletFact, News, Topic
from onegov.plausible.plausible_api import PlausibleAPI
from onegov.reservation import Reservation, ResourceCollection
from onegov.ticket import Ticket, TicketCollection

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Session

    from onegov.org.request import OrgRequest


class OrgBoardlet(Boardlet):

    request: OrgRequest

    @cached_property
    def session(self) -> Session:
        return self.request.session

    @cached_property
    def layout(self) -> DefaultLayout:
        return DefaultLayout(None, self.request)

    @cached_property
    def plausible_api(self) -> PlausibleAPI | None:
        provider = self.request.analytics_provider

        if isinstance(provider, Plausible):
            # NOTE: In the future we may want to support arbitrary Plausible
            #       instances, in which case the api token configuration would
            #       probably move to the analytics provider.
            if 'analytics.seantis.ch' in provider.configuration['script_src']:
                return PlausibleAPI(
                    provider.domain(self.request),
                    self.request.app.plausible_api_token
                )

        return None


@OrgApp.boardlet(name='ticket', order=(1, 1), icon='fa-ticket-alt')
class TicketBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Tickets')

    @property
    def facts(self) -> Iterator[BoardletFact]:
        time_30d_ago = utcnow() - timedelta(days=30)

        yield BoardletFact(
            text=_('Open Tickets'),
            number=self.session.query(Ticket).filter_by(
                state='open').count(),
            icon='fas fa-hourglass'
        )

        yield BoardletFact(
            text=_('Pending Tickets'),
            number=self.session.query(Ticket).filter_by(
                state='pending').count(),
            icon='fas fa-hourglass-half'
        )

        yield BoardletFact(
            text=_('New Tickets in the Last Month'),
            number=self.session.query(Ticket).filter(
                Ticket.created > time_30d_ago).count(),
            icon='fas fa-plus-circle'
        )

        closed_ticket_query = (
            self.session.query(Ticket).
            filter(Ticket.closed_on.isnot(None)).
            filter(Ticket.closed_on >= time_30d_ago))
        closed_tickets_count = closed_ticket_query.count()

        yield BoardletFact(
            text=_('Closed Tickets in the Last Month'),
            number=closed_tickets_count,
            icon='fas fa-check-circle'
        )

        # average lead time from opening to closing
        average_lead_time_s: float | None = None
        if closed_tickets_count:
            total_lead_time_s = sum(
                (t.reaction_time or 0) + (t.process_time or 0)
                for t in closed_ticket_query)
            average_lead_time_s = total_lead_time_s / closed_tickets_count
            average_lead_time_s = round(average_lead_time_s / 86400, 1)

        yield BoardletFact(
            text=_('Lead Time from opening to closing in Days '
                   'over the Last Month'),
            number=average_lead_time_s or '-',
            icon='fas fa-clock'
        )

        # average lead time from pending to closing
        average_lead_time_s = None
        if closed_tickets_count:
            total_lead_time_s = sum(
                t.process_time or 1 for t in closed_ticket_query)
            average_lead_time_s = total_lead_time_s / closed_tickets_count
            average_lead_time_s = round(average_lead_time_s / 86400, 1)

        yield BoardletFact(
            text=_('Lead Time from pending to closing in Days '
                   'over the Last Month'),
            number=average_lead_time_s or '-',
            icon='fas fa-clock'
        )


def get_icon_for_access_level(access: str) -> str:
    access_icons = {
        'public': 'fas fa-eye',
        'secret': 'fas fa-user-secret',
        'private': 'fas fa-lock',
        'member': 'fas fa-users'
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
class EditedTopicsBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Last Edited Topics')

    @property
    def facts(self) -> Iterator[BoardletFact]:

        last_edited_pages = self.session.query(Topic).order_by(
            Topic.last_change.desc()).limit(8)

        for p in last_edited_pages:
            yield BoardletFact(
                text='',
                link=(self.layout.request.link(p), p.title),
                icon='fas fa-file',
                visibility_icon=get_icon_for_access_level(p.access),
                icon_title=get_icon_title(self.request, p.access)
            )


@OrgApp.boardlet(name='news', order=(1, 3), icon='fa-edit')
class EditedNewsBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('Last Edited News')

    @property
    def facts(self) -> Iterator[BoardletFact]:
        last_edited_news = self.session.query(News).order_by(
            News.last_change.desc()).limit(8)

        for n in last_edited_news:
            yield BoardletFact(
                text='',
                link=(self.layout.request.link(n), n.title),
                icon='fas fa-newspaper',
                visibility_icon=get_icon_for_access_level(n.access),
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

        texts = [
            _('Unique Visitors in the Last Month'),
            _('Total Visits in the Last Month'),
            _('Total Page Views in the Last Month'),
            _('Number of Page Views per Visit'),
            _('Average Visit Duration in Minutes')
        ]

        results = self.plausible_api.get_stats()
        if not results:
            yield BoardletFact(
                text=_('No data available'),
                number=None
            )

        for text, value in zip(texts, results):
            yield BoardletFact(
                text=text,
                number=value
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


@OrgApp.boardlet(
    name='ticket',
    kind='citizen',
    order=(1, 1),
    icon='fa-ticket-alt'
)
class CitizenTicketBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('My Requests')

    @cached_property
    def url(self) -> str:
        return self.request.class_link(
            TicketCollection,
            {
                'handler': 'ALL',
                'state': 'all',
            },
            name='my-tickets'
        )

    @property
    def facts(self) -> Iterator[BoardletFact]:
        ticket_counts = dict(
            self.session.query(
                Ticket.state,
                func.count(Ticket.id)
            ).filter(
                func.lower(Ticket.ticket_email) == email.lower()
            ).group_by(Ticket.state)
        ) if (email := self.request.authenticated_email) else {}

        yield BoardletFact(
            text='',
            link=(self.url, _('Open Tickets')),
            number=ticket_counts.get('open', 0),
            icon='fas fa-hourglass'
        )

        yield BoardletFact(
            text='',
            link=(self.url, _('Pending Tickets')),
            number=ticket_counts.get('pending', 0),
            icon='fas fa-hourglass-half'
        )

        done_count = ticket_counts.get('closed', 0)
        done_count += ticket_counts.get('archived', 0)
        yield BoardletFact(
            text='',
            link=(self.url, _('Closed Tickets')),
            number=done_count,
            icon='fas fa-check-circle'
        )


@OrgApp.boardlet(
    name='reservation',
    kind='citizen',
    order=(1, 2),
    icon='fa-calendar fa-calendar-alt'
)
class CitizenReservationBoardlet(OrgBoardlet):

    @property
    def title(self) -> str:
        return _('My Reservations')

    @cached_property
    def reservation_counts(self) -> dict[tuple[bool, bool], int]:
        email = self.request.authenticated_email
        if not email:
            return {}

        subquery = self.session.query(
            Reservation.id.label('id'),
            (Reservation.start > utcnow()).label('future'),
            Reservation.data['accepted'].isnot(None).label('accepted')
        ).filter(
            func.lower(Reservation.email) == email.lower()
        ).subquery()
        return {
            (future, accepted): count
            for future, accepted, count in self.session.query(
                subquery.c.future,
                subquery.c.accepted,
                func.count(subquery.c.id)
            ).group_by(
                subquery.c.future,
                subquery.c.accepted
            )
        }

    @property
    def is_available(self) -> bool:
        return any(self.reservation_counts.values())

    @cached_property
    def url(self) -> str:
        return self.request.class_link(
            ResourceCollection,
            name='my-reservations'
        )

    @property
    def facts(self) -> Iterator[BoardletFact]:
        reservation_counts = self.reservation_counts

        yield BoardletFact(
            text='',
            link=(self.url, _('Pending Future Reservations')),
            number=reservation_counts.get((True, False), 0),
            icon='far fa-calendar fa-calendar-o'
        )

        yield BoardletFact(
            text='',
            link=(self.url, _('Confirmed Future Reservations')),
            number=reservation_counts.get((True, True), 0),
            icon='far fa-calendar-check fa-calendar-check-o'
        )

        past_count = reservation_counts.get((False, False), 0)
        past_count += reservation_counts.get((False, True), 0)
        yield BoardletFact(
            text='',
            link=(self.url, _('Past Reservations')),
            number=past_count,
            icon='far fa-calendar-minus fa-calendar-minus-o '
        )
