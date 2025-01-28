from __future__ import annotations
from datetime import timedelta
from functools import cached_property
from sedate import utcnow
from typing import TYPE_CHECKING

from onegov.org.layout import DefaultLayout
from onegov.org.models import Boardlet, BoardletFact, News
from onegov.page import Page
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

        time_7d_ago = utcnow() - timedelta(days=7)

        new_tickets = self.session.query(Ticket).filter(
            Ticket.created <= time_7d_ago).count()
        yield BoardletFact(
            text=_('New Tickets in the Last Week'),
            number=new_tickets,
            icon='fa-plus-circle'
        )

        closed_tickets = self.session.query(Ticket).filter_by(
            state='closed').filter(
            Ticket.last_change >= time_7d_ago).count()
        yield BoardletFact(
            text=_('Closed Tickets in the Last Week'),
            number=closed_tickets,
            icon='fa-check-circle'
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
