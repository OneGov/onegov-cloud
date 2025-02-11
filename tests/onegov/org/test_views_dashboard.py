import uuid
from unittest.mock import patch

import transaction

from onegov.org import OrgApp
from onegov.org.boardlets import OrgBoardlet
from onegov.plausible.plausible_api import PlausibleAPI
from onegov.ticket import TicketCollection
from onegov.user import User
from tests.onegov.core.test_sentry import monkeypatch_test_transport
from tests.onegov.ticket.test_collection import EchoHandler


def test_view_dashboard_no_access(client):
    # user cannot see the dashboard
    response = client.get('/dashboard', expect_errors=True)
    assert response.status_code == 403
    assert 'Zugriff verweigert' in response


def test_view_dashboard_no_ticket(client):
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
    assert 'Zuletzt bearbeitete Seiten' in page
    assert 'Zuletzt bearbeitete News' in page


def test_view_dashboard_tickets(session, handlers, client):
    handlers.register('EVN', EchoHandler)

    transaction.begin()

    editor = User(
        id=uuid.uuid4(),
        username='editor',
        password='editor',
        role='editor',
    )
    collection = TicketCollection(session)

    collection.open_ticket(
        handler_id='1',
        handler_code='EVN',
        title='Ticket After Work Beer',
        group='Event',
    )
    collection.open_ticket(
        handler_id='2',
        handler_code='EVN',
        title='Ticket Petting Zoo',
        group='Event',
    )
    collection.open_ticket(
        handler_id='3',
        handler_code='EVN',
        title='Ticket Cheese Fondue',
        group='Event',
    )

    transaction.commit()

    collection = TicketCollection(session)
    assert collection.query().count() == 3
    assert collection.query().filter_by(state='open').count() == 3

    client.login_admin()
    page = client.get('/dashboard')
    fact_numbers = page.pyquery('.fact-number').text()
    fact_numbers = fact_numbers.split(' ')
    assert fact_numbers == ['3', '0', '3', '0', '-', '-']

    transaction.begin()
    # accept one ticket
    collection.by_handler_id('1').accept_ticket(editor)
    # close another ticket
    collection.by_handler_id('2').accept_ticket(editor)
    collection.by_handler_id('2').close_ticket()
    # the third ticket remains open
    transaction.commit()

    collection = TicketCollection(session)
    assert collection.query().count() == 3
    assert collection.query().filter_by(state='open').count() == 1
    assert collection.query().filter_by(state='pending').count() == 1
    assert collection.query().filter_by(state='closed').count() == 1

    client.login_admin()
    page = client.get('/dashboard')
    fact_numbers = page.pyquery('.fact-number').text()
    fact_numbers = fact_numbers.split(' ')
    assert fact_numbers == ['1', '1', '3', '1', '-', '-']


def test_view_dashboard_topics_news(handlers, client):
    client.login_admin()
    page = client.get('/dashboard')

    assert page.pyquery('.boardlet').length == 3
    assert 'Tickets' in page
    assert 'Zuletzt bearbeitete Seiten' in page
    assert 'Zuletzt bearbeitete News' in page

    links = page.pyquery('.boardlet a')
    link_texts = []
    for link in links:
        link_texts.append(link.text)

    # Topics
    assert link_texts[0] == 'Wir haben eine neue Webseite!'
    assert link_texts[1] == 'Aktuelles'
    assert link_texts[2] == 'Kontakt'
    assert link_texts[3] == 'Themen'
    assert link_texts[4] == 'Organisation'
    # News
    assert link_texts[5] == 'Wir haben eine neue Webseite!'
    assert link_texts[6] == 'Aktuelles'


def test_view_dashboard_web_stats(client, monkeypatch):

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
                        PlausibleAPI('site_id'))
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
