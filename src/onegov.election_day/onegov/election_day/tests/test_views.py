import onegov.election_day
import transaction

from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import Subscriber
from onegov.election_day.tests import login
from onegov.election_day.tests import upload_majorz_election
from onegov.election_day.tests import upload_vote
from onegov.testing import utils
from webtest import TestApp as Client


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
    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadc0de' in anonymous.get('/', headers=[
        ('Cache-Control', 'no-cache')
    ])

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = '0xdeafbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeafbeef' not in anonymous.get('/')
    assert '0xdeafbeef' in anonymous.get(
        '/', headers=[('Cache-Control', 'no-cache')]
    )


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
            '/vote/vote/',
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

    upload_majorz_election(client, False)
    assert "erneut auslösen" not in client.get(
        '/election/majorz-election/trigger'
    )


def test_view_headerless(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, zg=True)

    ballot = election_day_app.session().query(Ballot).one().id

    for path in (
        '/',
        '/archive/2013',
        '/election/majorz-election',
        '/vote/vote',
    ):
        assert 'frame_resizer' not in client.get(path)
        assert 'frame_resizer' in client.get(path + '?headerless')
        assert 'frame_resizer' in client.get(path)
        assert 'frame_resizer' not in client.get(path + '?headerful')
        assert 'frame_resizer' not in client.get(path)

    for path in (
        '/archive/2013/json',
        '/election/majorz-election/candidates',
        '/election/majorz-election/connections',
        '/election/majorz-election/data-csv',
        '/election/majorz-election/data-json',
        '/election/majorz-election/data-xlsx',
        '/election/majorz-election/json',
        '/election/majorz-election/lists',
        '/election/majorz-election/summary',
        '/json',
        '/ballot/{}/by-entity'.format(ballot),
        '/vote/vote/data-csv',
        '/vote/vote/data-json',
        '/vote/vote/data-xlsx',
        '/vote/vote/json',
        '/vote/vote/summary',
    ):
        assert 'frame_resizer' not in client.get(path)
        assert 'frame_resizer' not in client.get(path + '?headerless')
        assert 'frame_resizer' not in client.get(path)
        assert 'frame_resizer' not in client.get(path + '?headerful')
        assert 'frame_resizer' not in client.get(path)

    for path in (
        '/election/majorz-election/candidates-chart',
        '/election/majorz-election/lists-chart',
        '/election/majorz-election/connections-chart',
        '/ballot/{}/map'.format(ballot),
    ):
        assert 'frame_resizer' in client.get(path)
        assert 'frame_resizer' in client.get(path + '?headerless')
        assert 'frame_resizer' in client.get(path)
        assert 'frame_resizer' in client.get(path + '?headerful')
        assert 'frame_resizer' in client.get(path)


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
