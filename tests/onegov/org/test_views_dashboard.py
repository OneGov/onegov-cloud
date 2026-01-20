from __future__ import annotations

import transaction

from onegov.org.boardlets import OrgBoardlet
from onegov.plausible.plausible_api import PlausibleAPI
from onegov.ticket import TicketCollection, Ticket
from onegov.user import User
from tests.onegov.org.conftest import EchoHandler

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pytest
    from onegov.ticket.handler import HandlerRegistry
    from .conftest import Client


def test_view_dashboard_no_access(client: Client) -> None:
    # user cannot see the dashboard
    response = client.get('/dashboard', expect_errors=True)
    assert response.status_code == 403
    assert 'Zugriff verweigert' in response


def test_view_dashboard_no_ticket(client: Client) -> None:
    client.login_admin()

    page = client.get('/dashboard')

    # expecting 3 boardlets
    assert page.pyquery('.boardlet').length == 3

    # tickets
    assert 'Offene Tickets' in page
    fact_numbers = page.pyquery('.fact-number').text()
    fact_numbers = fact_numbers.split(' ')
    assert len(fact_numbers) == 6
    assert fact_numbers[0] == '0'  # open tickets
    assert fact_numbers[1] == '0'  # closed tickets
    assert fact_numbers[2] == '0'  # new tickets
    assert fact_numbers[3] == '0'  # closed tickets last month
    assert fact_numbers[4] == '-'  # lead time opening to closing
    assert fact_numbers[5] == '-'  # lead time pending to closing

    # pages and news
    assert 'Zuletzt bearbeitete Themen' in page
    assert 'Zuletzt bearbeitete News' in page


def test_view_dashboard_tickets(
    handlers: HandlerRegistry,
    client: Client
) -> None:

    handlers.register('EVN', EchoHandler)

    session = client.app.session()

    session.add(User(
        username='user',
        password='password',
        role='admin'
    ))
    user = session.query(User).filter_by(username='user').first()
    assert user is not None

    tickets = [
        Ticket(
            number='EVN-0001',
            handler_id='1',
            handler_code='EVN',
            title='Ticket After Work Beer',
            group='Event',
            state='open'
        ),
        Ticket(
            number='EVN-0002',
            handler_id='2',
            handler_code='EVN',
            title='Ticket Petting Zoo',
            group='Event',
            state='open'
        ),
        Ticket(
            number='EVN-0003',
            handler_id='3',
            handler_code='EVN',
            title='Ticket Cheese Fondue',
            group='Event',
            state='open'
        )
    ]

    for ticket in tickets:
        session.add(ticket)

    collection = TicketCollection(session)

    collection.by_handler_id('2').accept_ticket(user)  # type: ignore[union-attr]
    collection.by_handler_id('3').accept_ticket(user)  # type: ignore[union-attr]

    collection.by_handler_id('3').close_ticket()  # type: ignore[union-attr]

    transaction.commit()

    collection = TicketCollection(session)
    count = collection.get_count()
    assert count.open == 1
    assert count.pending == 1
    assert count.closed == 1
    assert collection.query().count() == 3
    assert collection.query().filter_by(state='open').count() == 1
    assert collection.query().filter_by(state='pending').count() == 1
    assert collection.query().filter_by(state='closed').count() == 1

    client.login_admin()
    page = client.get('/dashboard')
    assert page.pyquery('.boardlet').length == 3
    assert 'Tickets' in page
    assert 'Zuletzt bearbeitete Themen' in page
    assert 'Zuletzt bearbeitete News' in page
    fact_numbers = page.pyquery('.fact-number').text()
    fact_numbers = fact_numbers.split()
    assert fact_numbers == ['1', '1', '3', '1', '-', '-']

    # cross-check with ticket menu
    assert page.pyquery('.open-tickets').attr('data-count') == '1'
    assert page.pyquery('.pending-tickets').attr('data-count') == '1'
    assert page.pyquery('.closed-tickets').attr('data-count') == '1'


def test_view_dashboard_topics_news(
    handlers: HandlerRegistry,
    client: Client
) -> None:

    client.login_admin()
    page = client.get('/dashboard')

    assert page.pyquery('.boardlet').length == 3
    assert 'Tickets' in page
    assert 'Zuletzt bearbeitete Themen' in page
    assert 'Zuletzt bearbeitete News' in page

    links = page.pyquery('.boardlet a')
    link_texts = []
    for link in links:
        link_texts.append(link.text)

    # Topics
    assert link_texts[0] == 'Kontakt'
    assert link_texts[1] == 'Themen'
    assert link_texts[2] == 'Organisation'
    # News
    assert link_texts[3] == 'Wir haben eine neue Webseite!'
    assert link_texts[4] == 'Aktuelles'


def test_view_dashboard_web_stats(
    client: Client,
    monkeypatch: pytest.MonkeyPatch
) -> None:

    page_metrics = [10, 15, 20, 25, 30]
    pages = [
        '/'
        '/page_1',
        '/topic/test/page2',
        '/topic/test/subtest/page3',
        '/news/news1',
    ]

    # each get on '/dashboard' will return two responses
    mock_responses = iter([
        {
            'results': [],
        },
        {
            'results': [],
        },
        {
            'results': [
                {'metrics': [100, 200, 300, 4, 600],
                 'dimensions': ['visitors', 'visits', 'pageviews',
                                'views_per_visit', 'visit_duration']}
            ]
        },
        {
            'results': [
                {'metrics': [metric], 'dimensions': [page]}
                for metric, page in zip(page_metrics, pages)
            ]
        }
    ])

    monkeypatch.setattr(OrgBoardlet, 'plausible_api',
                        PlausibleAPI('site_id', 'my-token'))
    monkeypatch.setattr(PlausibleAPI, '_send_request',
                        lambda x, payload: next(mock_responses))

    client.login_admin()

    # no data
    stats = client.get('/dashboard')
    assert 'Web-Statistik' in stats
    assert stats.pyquery('.boardlet').length == 5
    assert 'Keine Daten verfügbar' in stats

    # with data
    stats = client.get('/dashboard')
    assert 'Web-Statistik' in stats
    assert stats.pyquery('.boardlet').length == 5

    # Web stats
    assert 'Web-Statistik' in stats
    assert 'Einzigartige Besucher im letzten Monat' in stats
    assert '100' in stats
    assert 'Gesamtbesuche im letzten Monat' in stats
    assert '200' in stats
    assert 'Gesamtseitenaufrufe im letzten Monat' in stats
    assert '300' in stats
    assert 'Anzahl der Seitenaufrufe pro Besuch' in stats
    assert '4' in stats
    assert 'Durchschnittliche Besuchsdauer in Minuten' in stats
    assert '10.0' in stats  # 600 seconds converted to 10.0 minutes

    # Most popular pages
    assert 'Beliebteste Seiten' in stats
    for visits, page in zip(page_metrics, pages):
        assert str(visits) in stats
        assert page in stats
