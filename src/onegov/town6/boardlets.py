from __future__ import annotations

from datetime import timedelta
from functools import cached_property

import requests
from requests import HTTPError
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

        # TODO: add average ticket lead time from opening to closing
        # TODO: add average ticket lead time from pending/in progress to
        #  closing


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


def plausible_stats(
    metrics: list[str],
    date_range: str,
    filters: list[str] | None = None,
    dimensions: list[str] | None = None
) -> dict[str, list[dict[str, str]]]:
    api_key = (
        'eR9snr0RzrglMLrKqVPNQ_IYL3dD6hyOX0-2gyRMlxSSSTk5bg6NjORWtbNEMoHU')
    site_id = 'wil.onegovcloud.ch'

    if filters is None:
        filters = []
    if dimensions is None:
        dimensions = []

    url = 'https://analytics.seantis.ch/api/v2/query'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'site_id': site_id,
        'metrics': metrics,
        'date_range': date_range,
        'filters': filters,
        'dimensions': dimensions
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes
    except HTTPError as e:
        if response.status_code == 401:
            print('Unauthorized: Invalid API key or insufficient '
                  'permissions', e)
        else:
            print('HTTP error', e)
    except Exception as e:
        print('Plausible error occurred:', e)

    print('*** tschupre get plausible stats response', response.json())
    return response.json()


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


@TownApp.boardlet(name='plausible-stats', order=(2, 1))
class PlausibleStats(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Plausible Stats'

    @property
    def facts(self) -> Iterator[BoardletFact]:

        data = plausible_stats(
            ['visitors', 'pageviews', 'views_per_visit',
             'visit_duration'],
            '7d',
        )

        values = data['results'][0]['metrics']

        yield BoardletFact(
            text='Unique Visitors in the Last Week',
            number=values[0] or '-',
        )

        yield BoardletFact(
            text='Total Page Views in the Last Week',
            number=values[1] or '-',
        )

        yield BoardletFact(
            text='Number of Page Views per Visit',
            number=values[2] or '-',
        )

        yield BoardletFact(
            text='Average Visit Duration in Seconds',
            number=values[3] or '-',
        )


@TownApp.boardlet(name='Top Pages', order=(2, 2))
class PlausibleTopPages(TownBoardlet):

    @property
    def title(self) -> str:
        return 'Top Pages'

    @property
    def facts(self) -> Iterator[BoardletFact]:

        data = plausible_stats(
            ['visitors'],
            '7d',
            [],
            ['event:page']
        )

        # Extract and sort the results by the number of visits (metrics)
        sorted_results = sorted(
            data['results'], key=lambda x: x['metrics'][0], reverse=True)

        # Print the sorted results
        for result in sorted_results[:10]:
            print(f"Top Page: {result['dimensions'][0]}, Visits:"
                  f" {result['metrics'][0]}")
            yield BoardletFact(
                text=result['dimensions'][0],
                number=result['metrics'][0] or '-',
            )
