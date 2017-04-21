import onegov.election_day
import transaction

from datetime import date
from freezegun import freeze_time
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import Subscriber
from onegov.election_day.tests import login
from onegov.election_day.tests import upload_majorz_election
from onegov.election_day.tests import upload_proporz_election
from onegov.election_day.tests import upload_vote
from onegov.testing import utils
from webtest import TestApp as Client
from unittest.mock import patch


COLUMNS = [
    'Bezirk',
    'BFS Nummer',
    'Gemeinde',
    'Ja Stimmen',
    'Nein Stimmen',
    'Stimmberechtigte',
    'Leere Stimmzettel',
    'Ungültige Stimmzettel'
]


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.election_day, onegov.election_day.ElectionDayApp)


def test_view_login_logout(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/').click('Anmelden')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter1'

    assert "Unbekannter Benutzername oder falsches Passwort" \
        in login.form.submit()
    assert 'Anmelden' in client.get('/')

    login.form['password'] = 'hunter2'
    homepage = login.form.submit().follow()

    assert 'Sie sind angemeldet' in homepage
    assert 'Abmelden' in homepage
    assert 'Anmelden' not in homepage

    assert 'Anmelden' in client.get('/').click('Abmelden').follow()


def test_view_manage(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage/elections',
                      expect_errors=True).status_code == 403
    assert client.get('/manage/votes', expect_errors=True).status_code == 403

    login(client)

    manage = client.get('/manage/elections')

    assert "Noch keine Wahlen erfasst" in manage

    new = manage.click('Neue Wahl')
    new.form['election_de'] = 'Elect a new president'
    new.form['date'] = date(2016, 1, 1)
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['mandates'] = 1
    manage = new.form.submit().follow()

    last_result_change = archive.query().one().last_result_change

    assert "Elect a new president" in manage
    edit = manage.click('Bearbeiten')
    edit.form['election_de'] = 'Elect a new federal councillor'
    edit.form['absolute_majority'] = None
    manage = edit.form.submit().follow()

    assert "Elect a new federal councillor" in manage
    assert "Elect a new federal councillor" == archive.query().one().title
    assert last_result_change != archive.query().one().last_result_change

    delete = manage.click("Löschen")
    assert "Wahl löschen" in delete
    assert "Elect a new federal councillor" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Wahlen erfasst" in manage

    assert archive.query().count() == 0

    manage = client.get('/manage/votes')

    assert "Noch keine Abstimmungen erfasst" in manage

    new = manage.click('Neue Abstimmung')
    new.form['vote_de'] = 'Vote for a better yesterday'
    new.form['date'] = date(2016, 1, 1)
    new.form['domain'] = 'federation'
    manage = new.form.submit().follow()

    last_result_change = archive.query().one().last_result_change

    assert "Vote for a better yesterday" in manage
    edit = manage.click('Bearbeiten')
    edit.form['vote_de'] = 'Vote for a better tomorrow'
    manage = edit.form.submit().follow()

    assert "Vote for a better tomorrow" in manage
    assert "Vote for a better tomorrow" == archive.query().one().title
    assert last_result_change != archive.query().one().last_result_change

    delete = manage.click("Löschen")
    assert "Abstimmung löschen" in delete
    assert "Vote for a better tomorrow" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Abstimmungen erfasst" in manage

    assert archive.query().count() == 0


def test_i18n(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Foo'
    new.form['vote_fr'] = 'Bar'
    new.form['vote_it'] = 'Baz'
    new.form['vote_rm'] = 'Qux'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    homepage = client.get('/')
    assert "Foo" in homepage

    homepage = homepage.click('Français').follow()
    assert "Bar" in homepage

    homepage = homepage.click('Italiano').follow()
    assert "Baz" in homepage

    homepage = homepage.click('Rumantsch').follow()
    assert "Qux" in homepage

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Tick'
    new.form['election_fr'] = 'Trick'
    new.form['election_it'] = 'Track'
    new.form['election_rm'] = 'Quack'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    homepage = client.get('/')
    assert "Quack" in homepage

    homepage = homepage.click('Français').follow()
    assert "Trick" in homepage

    homepage = homepage.click('Italiano').follow()
    assert "Track" in homepage

    homepage = homepage.click('Deutsch').follow()
    assert "Tick" in homepage


def test_pages_cache(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH')

    # make sure codes != 200 are not cached
    anonymous = Client(election_day_app)
    anonymous.get('/vote/0xdeadbeef', status=404)
    anonymous.get('/election/0xdeafbeef', status=404)

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = '0xdeadbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef')

    edit = client.get('/vote/0xdeadbeef/edit')
    edit.form['vote_de'] = '0xdeadc0de'
    edit.form.submit()

    assert '0xdeadc0de' in client.get('/')
    assert '0xdeadc0de' in anonymous.get('/')
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef')
    assert '0xdeadc0de' in anonymous.get('/vote/0xdeadbeef', headers=[
        ('Cache-Control', 'no-cache')
    ])


def test_view_latest(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    latest = client.get('/')
    assert "Abstimmung 1. Januar 2013" in latest
    assert "Wahl 1. Januar 2013" in latest


def test_view_latest_json(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    assert client.get('/json').json['archive'] == {}
    assert client.get('/json').json['results'] == []

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    latest = client.get('/json')
    assert list(latest.json['archive'].keys()) == ['2013']
    assert "Abstimmung 1. Januar 2013" in latest
    assert "Wahl 1. Januar 2013" in latest


def test_view_archive(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "archive/2013" in client.get('/')

    archive = client.get('/archive/2013')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-02-02')
    assert "noch keine Wahlen oder Abstimmungen" in archive


def test_view_archive_json(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    archive = client.get('/archive/2013/json')
    assert list(archive.json['archive'].keys()) == ['2013']
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01/json')
    assert list(archive.json['archive'].keys()) == ['2013']
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-02-02/json')
    assert list(archive.json['archive'].keys()) == ['2013']
    assert archive.json['results'] == []


def test_view_last_modified(election_day_app):
    with freeze_time("2014-01-01 12:00"):
        client = Client(election_day_app)
        client.get('/locale/de_CH').follow()

        login(client)

        new = client.get('/manage/votes/new-vote')
        new.form['vote_de'] = "Vote"
        new.form['date'] = date(2013, 1, 1)
        new.form['domain'] = 'federation'
        new.form.submit()

        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = "Election"
        new.form['date'] = date(2013, 1, 1)
        new.form['mandates'] = 1
        new.form['election_type'] = 'majorz'
        new.form['domain'] = 'federation'
        new.form.submit()

        client = Client(election_day_app)
        client.get('/locale/de_CH').follow()

        for path in (
            '/json',
            '/election/election/summary',
            '/election/election/json',
            '/election/election/data-json',
            '/election/election/data-csv',
            '/election/election/data-xlsx',
            '/vote/vote/summary',
            '/vote/vote/json',
            '/vote/vote/data-json',
            '/vote/vote/data-csv',
            '/vote/vote/data-xlsx',
        ):
            assert client.get(path).headers.get('Last-Modified') == \
                'Wed, 01 Jan 2014 12:00:00 GMT'

        for path in (
            '/'
            '/archive/2013',
            '/election/election',
            '/election/election/lists',
            '/election/election/candidates',
            '/election/election/statistics',
            '/election/election/districts',
            '/vote/vote/',
            '/vote/vote/counter-proposal',
            '/vote/vote/tie-breaker',
        ):
            assert 'Last-Modified' not in client.get(path).headers


def test_view_notifications_votes(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Vote"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Benachrichtigungen auslösen" not in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" not in upload_vote(client, False)

    election_day_app.principal.webhooks = ['http://example.com/1']

    assert "Benachrichtigungen auslösen" in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" in upload_vote(client, False)

    assert "erneut auslösen" not in client.get('/vote/vote/trigger')
    client.get('/vote/vote/trigger').form.submit()
    assert "erneut auslösen" in client.get('/vote/vote/trigger')

    upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')


def test_view_notifications_elections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Majorz Election"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Benachrichtigungen auslösen" not in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" not in upload_majorz_election(
        client, False
    )

    election_day_app_gr.principal.webhooks = ['http://example.com/1']

    assert "Benachrichtigungen auslösen" in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" in upload_majorz_election(
        client, False
    )

    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )
    client.get('/election/majorz-election/trigger').form.submit()
    assert "erneut auslösen" in client.get('/election/majorz-election/trigger')

    results = archive.query().count() == 2
    assert len(client.get('/json').json['results']) == 2


def test_view_notifications_votes(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Vote"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Benachrichtigungen auslösen" not in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" not in upload_vote(client, False)

    election_day_app.principal.webhooks = {'http://example.com/1': None}
    del election_day_app.principal.notifications

    assert "Benachrichtigungen auslösen" in client.get('/manage/votes')
    assert "Benachrichtigungen auszulösen" in upload_vote(client, False)

    assert "erneut auslösen" not in client.get('/vote/vote/trigger')
    client.get('/vote/vote/trigger').form.submit()
    assert "erneut auslösen" in client.get('/vote/vote/trigger')

    upload_vote(client, False)
    assert "erneut auslösen" not in client.get('/vote/vote/trigger')


def test_view_notifications_elections(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Majorz Election"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Benachrichtigungen auslösen" not in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" not in upload_majorz_election(
        client, False
    )

    election_day_app_gr.principal.webhooks = {'http://example.com/1': None}
    del election_day_app_gr.principal.notifications

    assert "Benachrichtigungen auslösen" in client.get('/manage/elections')
    assert "Benachrichtigungen auszulösen" in upload_majorz_election(
        client, False
    )

    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )
    client.get('/election/majorz-election/trigger').form.submit()
    assert "erneut auslösen" in client.get('/election/majorz-election/trigger')

    upload_majorz_election(client)
    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )


def test_view_headerless(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')

    for path in (
        '/',
        '/archive/2013',
        '/election/majorz-election/candidates',
        '/election/majorz-election/districts',
        '/election/majorz-election/statistics',
        '/election/majorz-election/data',
        '/vote/vote',
    ):
        assert 'manage-links' in client.get(path)
        assert 'manage-links' not in client.get(path + '?headerless')
        assert 'manage-links' not in client.get(path)
        assert 'manage-links' in client.get(path + '?headerful')
        assert 'manage-links' in client.get(path)


def test_view_subscription(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe')
    subscribe.form['phone_number'] = 'abcd'
    subscribe = subscribe.form.submit()
    assert "Ungültige Telefonnummer" in subscribe

    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app.session().query(Subscriber).one().locale == 'de_CH'

    client.get('/locale/fr_CH').follow()

    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert election_day_app.session().query(Subscriber).one().locale == 'fr_CH'

    client.get('/locale/de_CH').follow()

    login(client)
    assert '+41791112233' in client.get('/manage/subscribers')
    assert 'fr_CH' in client.get('/manage/subscribers')

    unsubscribe = client.get('/unsubscribe')
    unsubscribe.form['phone_number'] = 'abcd'
    unsubscribe = unsubscribe.form.submit()
    assert "Ungültige Telefonnummer" in unsubscribe

    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe

    unsubscribe.form['phone_number'] = '0791112233'
    unsubscribe = unsubscribe.form.submit()
    assert "SMS-Benachrichtigung wurde beendet." in unsubscribe


def test_view_manage_subscription(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    subscribe = client.get('/subscribe')
    subscribe.form['phone_number'] = '0791112233'
    subscribe = subscribe.form.submit()
    assert "SMS-Benachrichtigung wurde abonniert" in subscribe
    assert election_day_app.session().query(Subscriber).one().locale == 'de_CH'

    login(client)
    manage = client.get('/manage/subscribers')
    assert '+41791112233' in manage

    manage = manage.click('Löschen').click('Abbrechen')
    assert '+41791112233' in manage

    manage = manage.click('Löschen').form.submit()
    assert '+41791112233' not in manage


def test_view_pdf(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')
    upload_proporz_election(client, canton='zg')

    paths = (
        '/vote/vote/pdf',
        '/election/majorz-election/pdf',
        '/election/proporz-election/pdf',
    )
    for path in paths:
        assert client.get(path, expect_errors=True).status_code == 503

    pdf = '%PDF-1.6'.encode('utf-8')
    election_day_app.filestorage.makedir('pdf')
    with election_day_app.filestorage.open('pdf/test.pdf', 'wb') as f:
        f.write(pdf)

    filenames = []
    with patch('onegov.election_day.layout.pdf_filename',
               return_value='test.pdf'):
        for path in paths:
            result = client.get(path)
            assert result.body == pdf
            assert result.headers['Content-Type'] == 'application/pdf'
            assert result.headers['Content-Length'] == '8'
            assert result.headers['Content-Disposition'].startswith(
                'inline; filename='
            )
            filenames.append(
                result.headers['Content-Disposition'].split('filename=')[1]
            )

    assert sorted(filenames) == [
        'majorz-election.pdf',
        'proporz-election.pdf',
        'vote.pdf'
    ]


def test_view_svg(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')
    upload_proporz_election(client, canton='zg')

    paths = (
        client.get('/vote/vote/json').json['media']['maps']['proposal'],
        '/election/majorz-election/candidates-svg',
        '/election/proporz-election/lists-svg',
        '/election/proporz-election/candidates-svg',
        '/election/proporz-election/panachage-svg',
        '/election/proporz-election/connections-svg',
        '/election/proporz-election/parties-svg',
    )
    for path in paths:
        assert client.get(path, expect_errors=True).status_code == 503

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.0" ></svg>'
    ).encode('utf-8')
    election_day_app.filestorage.makedir('svg')
    with election_day_app.filestorage.open('svg/test.svg', 'wb') as f:
        f.write(svg)

    filenames = []
    with patch('onegov.election_day.layout.svg_filename',
               return_value='test.svg'):
        for path in paths:
            result = client.get(path)
            assert result.body == svg
            assert result.headers['Content-Type'] == (
                'application/svg; charset=utf-8'
            )
            assert result.headers['Content-Length'] == '99'
            assert result.headers['Content-Disposition'].startswith(
                'inline; filename='
            )
            filenames.append(
                result.headers['Content-Disposition'].split('filename=')[1]
            )

    assert sorted(filenames) == [
        'majorz-election-candidates.svg',
        'proporz-election-candidates.svg',
        'proporz-election-list-connections.svg',
        'proporz-election-lists.svg',
        'proporz-election-panachage.svg',
        'proporz-election-parties.svg',
        'vote-proposal.svg'
    ]


def test_view_manage_data_sources(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()
    login(client)

    # Votes
    # ... add data source
    new = client.get('/manage/sources/new-source')
    new.form['name'] = 'ds_vote'
    new.form['upload_type'] = 'vote'
    new.form.submit().follow()
    assert 'ds_vote' in client.get('/manage/sources')

    # ... regenerate token
    manage = client.get('/manage/sources')
    token = manage.pyquery('.data_sources td')[2].text
    manage = manage.click('Token neu erzeugen').form.submit().follow()
    assert token not in manage

    # ... manage
    manage = manage.click('Verwalten', href='data-source').follow()

    assert 'Noch keine Abstimmungen erfasst' in manage.click('Neue Zuordnung')

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "vote-1"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "vote-2"
    new.form['date'] = date(2014, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = manage.click('Neue Zuordnung')
    assert all((x in new for x in ('vote-1', 'vote-2')))
    new.form['district'] = '1111'
    new.form['number'] = '2222'
    new.form['item'] = 'vote-1'
    manage = new.form.submit().follow()
    assert all((x in manage for x in ('vote-1', '1111', '2222')))

    edit = manage.click('Bearbeiten')
    edit.form['district'] = '3333'
    edit.form['number'] = '4444'
    edit.form['item'] = 'vote-2'
    manage = edit.form.submit().follow()
    assert all((x not in manage for x in ('vote-1', '1111', '2222')))
    assert all((x in manage for x in ('vote-2', '3333', '4444')))

    manage = manage.click('Löschen').form.submit().follow()
    assert 'Noch keine Zuordnungen' in manage

    # ... delete data source
    client.get('/manage/sources').click('Löschen').form.submit()
    assert 'ds_vote' not in client.get('/manage/sources')
    assert 'Noch keine Datenquellen' in client.get('/manage/sources')

    # Majorz elections
    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "election-majorz"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "election-proporz"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    # ... add data source
    new = client.get('/manage/sources/new-source')
    new.form['name'] = 'ds_majorz'
    new.form['upload_type'] = 'majorz'
    new.form.submit().follow()
    assert 'ds_majorz' in client.get('/manage/sources')

    # ... manage
    manage = client.get('/manage/sources')
    manage = manage.click('Verwalten', href='data-source').follow()

    new = manage.click('Neue Zuordnung')
    assert 'election-majorz' in new
    assert 'election-proporz' not in new
    new.form['district'] = '4444'
    new.form['number'] = '5555'
    new.form['item'] = 'election-majorz'
    manage = new.form.submit().follow()
    assert all((x in manage for x in ('election-majorz', '4444', '5555')))

    # ... delete data source
    client.get('/manage/sources').click('Löschen').form.submit()
    assert 'ds_majorz' not in client.get('/manage/sources')
    assert 'Noch keine Datenquellen' in client.get('/manage/sources')

    # Proporz elections
    # ... add data source
    new = client.get('/manage/sources/new-source')
    new.form['name'] = 'ds_proporz'
    new.form['upload_type'] = 'proporz'
    new.form.submit().follow()
    assert 'ds_proporz' in client.get('/manage/sources')

    # ... manage
    manage = client.get('/manage/sources')
    manage = manage.click('Verwalten', href='data-source').follow()

    new = manage.click('Neue Zuordnung')
    assert 'election-majorz' not in new
    assert 'election-proporz' in new
    new.form['district'] = '6666'
    new.form['number'] = '7777'
    new.form['item'] = 'election-proporz'
    manage = new.form.submit().follow()
    assert all((x in manage for x in ('election-proporz', '6666', '7777')))

    # ... delete data source
    client.get('/manage/sources').click('Löschen').form.submit()
    assert 'ds_proporz' not in client.get('/manage/sources')
    assert 'Noch keine Datenquellen' in client.get('/manage/sources')
