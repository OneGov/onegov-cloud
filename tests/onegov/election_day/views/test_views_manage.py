import os

from freezegun import freeze_time
from lxml.html import document_fromstring
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import ProporzElection
from tests.onegov.election_day.common import DummyRequest
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import logout
from tests.onegov.election_day.common import upload_election_compound
from tests.onegov.election_day.common import upload_majorz_election
from tests.onegov.election_day.common import upload_party_results
from tests.onegov.election_day.common import upload_proporz_election
from tests.onegov.election_day.common import upload_vote
from tests.shared import Client


def test_view_login_logout(election_day_app_zg):
    client = Client(election_day_app_zg)
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


def test_view_manage_elections(election_day_app_zg):
    archive = ArchivedResultCollection(election_day_app_zg.session())
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage/elections',
                      expect_errors=True).status_code == 403

    login(client)

    manage = client.get('/manage/elections')
    assert "Noch keine Wahlen erfasst" in manage

    # Add
    new = manage.click('Neue Wahl')
    new.form['title_de'] = 'Elect a new president'
    new.form['date'] = '2016-01-01'
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['mandates'] = 1
    manage = new.form.submit().follow()
    assert "Elect a new president" in manage

    # Edit
    edit = manage.click('Bearbeiten')
    edit.form['title_de'] = 'Elect a new federal councillor'
    edit.form['absolute_majority'] = None
    manage = edit.form.submit().follow()
    assert "Elect a new federal councillor" in manage
    assert "Elect a new federal councillor" == archive.query().one().title

    # Change ID
    change = manage.click('Bearbeiten')
    change.form['id'] = 'presidential-election'
    manage = change.form.submit().follow()
    assert '/election/presidential-election' in manage

    # Clear media
    clear = manage.click('Medien löschen')
    manage = clear.form.submit().follow()
    assert 'Dateien gelöscht.' in manage

    # Delete
    delete = manage.click("Löschen")
    assert "Wahl löschen" in delete
    assert "Elect a new federal councillor" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")
    manage = delete.form.submit().follow()
    assert "Noch keine Wahlen erfasst" in manage
    assert archive.query().count() == 0


def test_view_manage_election_compounds(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage/election-compounds',
                      expect_errors=True).status_code == 403

    login(client)

    manage = client.get('/manage/election-compounds')
    assert "Noch keine Verbindungen" in manage

    # Add two elections
    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['title_de'] = 'Elect a new parliament (Region A)'
    new.form['date'] = '2016-01-01'
    new.form['type'] = 'proporz'
    new.form['domain'] = 'region'
    new.form['mandates'] = 10
    new.form.submit().follow()

    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['title_de'] = 'Elect a new parliament (Region B)'
    new.form['date'] = '2016-01-01'
    new.form['type'] = 'proporz'
    new.form['domain'] = 'region'
    new.form['mandates'] = 5
    new.form.submit().follow()

    # Add a compound
    new = client.get('/manage/election-compounds').click('Neue Verbindung')
    new.form['title_de'] = 'Elect a new parliament'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'region'
    new.form['region_elections'] = ['elect-a-new-parliament-region-a']
    manage = new.form.submit().follow()
    assert "Elect a new parliament" in manage

    # Edit
    edit = manage.click('Bearbeiten')
    edit.form['title_de'] = 'Elect a new cantonal parliament'
    edit.form['region_elections'] = [
        'elect-a-new-parliament-region-a',
        'elect-a-new-parliament-region-b'
    ]
    manage = edit.form.submit().follow()
    assert "Elect a new cantonal parliament" in manage
    assert "Elect a new cantonal parliament" in [
        a.title for a in archive.query()
    ]

    # Change ID
    change = manage.click('Bearbeiten')
    change.form['id'] = 'parliamentary-election'
    manage = change.form.submit().follow()
    assert '/elections/parliamentary-election' in manage

    # Clear media
    clear = manage.click('Medien löschen')
    manage = clear.form.submit().follow()
    assert 'Dateien gelöscht.' in manage

    # Delete
    delete = manage.click("Löschen")
    assert "Verbindung löschen" in delete
    assert "Elect a new cantonal parliament" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")
    manage = delete.form.submit().follow()
    assert "Noch keine Verbindungen" in manage
    assert archive.query().count() == 2


def test_view_manage_votes(election_day_app_zg):
    archive = ArchivedResultCollection(election_day_app_zg.session())
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage/votes', expect_errors=True).status_code == 403

    login(client)

    manage = client.get('/manage/votes')
    assert "Noch keine Abstimmungen erfasst" in manage

    # Add
    new = manage.click('Neue Abstimmung')
    new.form['title_de'] = 'Vote for a better yesterday'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'federation'
    manage = new.form.submit().follow()
    assert "Vote for a better yesterday" in manage

    # Edit
    edit = manage.click('Bearbeiten')
    edit.form['title_de'] = 'Vote for a better tomorrow'
    manage = edit.form.submit().follow()
    assert "Vote for a better tomorrow" in manage
    assert "Vote for a better tomorrow" == archive.query().one().title

    # Change ID
    change = manage.click('Bearbeiten')
    change.form['id'] = 'future-vote'
    manage = change.form.submit().follow()
    assert '/vote/future-vote' in manage

    # Clear media
    clear = manage.click('Medien löschen')
    manage = clear.form.submit().follow()
    assert 'Dateien gelöscht.' in manage

    # Delete
    delete = manage.click("Löschen")
    assert "Abstimmung löschen" in delete
    assert "Vote for a better tomorrow" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")
    manage = delete.form.submit().follow()
    assert "Noch keine Abstimmungen erfasst" in manage
    assert archive.query().count() == 0


def test_upload_proporz_election(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_proporz_election(client, canton='zg')

    session = election_day_app_zg.session_manager.session()
    election = session.query(ProporzElection).one()
    assert election.type == 'proporz'

    request = DummyRequest(session, election_day_app_zg)

    layout = ElectionLayout(election, request, 'lists-panachage')
    assert layout.visible


def test_view_clear_results(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    with freeze_time('2023-01-01'):
        upload_majorz_election(client, canton='zg')
        upload_proporz_election(client, canton='zg')
        upload_election_compound(client, canton='zg')
        upload_party_results(client)
        upload_party_results(client, slug='elections/elections')
        upload_vote(client, canton='zg')

    urls = (
        '/election/majorz-election/candidates',
        '/election/majorz-election/statistics',
        '/election/proporz-election/lists',
        '/election/proporz-election/candidates',
        '/election/proporz-election/connections',
        '/election/proporz-election/party-strengths',
        '/election/proporz-election/parties-panachage',
        '/election/proporz-election/lists-panachage',
        '/election/proporz-election/statistics',
        '/elections/elections/districts',
        '/elections/elections/candidates',
        '/elections/elections/statistics',
        '/elections/elections/parties-panachage',
        '/elections/elections/party-strengths',
        '/elections/elections/seat-allocation',
        '/vote/vote/entities'
    )

    assert all(['Noch keine Resultate' not in client.get(url) for url in urls])
    assert '01.01.2023' in client.get('/archive/2022')

    client.get('/election/majorz-election/clear').form.submit().follow()
    client.get('/election/proporz-election/clear').form.submit().follow()
    client.get('/elections/elections/clear').form.submit().follow()
    client.get('/election/regional-election-a/clear').form.submit().follow()
    client.get('/election/regional-election-b/clear').form.submit().follow()
    client.get('/vote/vote/clear').form.submit().follow()

    assert all(['Noch keine Resultate' in client.get(url) for url in urls])
    assert '01.01.2023' not in client.get('/archive/2022')


def test_view_manage_upload_tokens(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()
    login(client)

    assert "Noch keine Token." in client.get('/manage/upload-tokens')

    client.get('/manage/upload-tokens/create-token').form.submit()
    assert "Noch keine Token." not in client.get('/manage/upload-tokens')

    client.get('/manage/upload-tokens').click("Löschen").form.submit()

    assert "Noch keine Token." in client.get('/manage/upload-tokens')


def test_view_manage_data_sources(election_day_app_zg):
    client = Client(election_day_app_zg)
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
    new.form['title_de'] = "vote-1"
    new.form['date'] = '2013-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = "vote-2"
    new.form['date'] = '2014-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = manage.click('Neue Zuordnung')
    assert all((x in new for x in ('vote-1', 'vote-2')))
    new.form['district'] = '1111'
    new.form['number'] = '2222'
    new.form['item'] = 'vote-1'
    manage = new.form.submit().follow()
    assert all((x in manage for x in ('vote-1', '>1111<', '>2222<')))

    edit = manage.click('Bearbeiten')
    edit.form['district'] = '3333'
    edit.form['number'] = '4444'
    edit.form['item'] = 'vote-2'
    manage = edit.form.submit().follow()
    assert all((x not in manage for x in ('vote-1', '>1111<', '>2222<')))
    assert all((x in manage for x in ('vote-2', '>3333<', '>4444<')))

    manage = manage.click('Löschen').form.submit().follow()
    assert 'Noch keine Zuordnungen' in manage

    # ... delete data source
    client.get('/manage/sources').click('Löschen').form.submit()
    assert 'ds_vote' not in client.get('/manage/sources')
    assert 'Noch keine Datenquellen' in client.get('/manage/sources')

    # Majorz elections
    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = "election-majorz"
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = "election-proporz"
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'proporz'
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
    assert all((x in manage for x in ('election-majorz', '>4444<', '>5555<')))

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
    assert all((x in manage for x in ('election-proporz', '>6666<', '>7777<')))

    # ... delete data source
    client.get('/manage/sources').click('Löschen').form.submit()
    assert 'ds_proporz' not in client.get('/manage/sources')
    assert 'Noch keine Datenquellen' in client.get('/manage/sources')


def test_reset_password(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    request_page = client.get('/auth/login').click('Passwort zurücksetzen')
    assert 'Passwort zurücksetzen' in request_page

    request_page.form['email'] = 'someone@example.org'
    assert 'someone@example.org' in request_page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 0

    request_page.form['email'] = 'admin@example.org'
    assert 'admin@example.org' in request_page.form.submit()
    assert len(os.listdir(client.app.maildir)) == 1

    message = client.get_email(0)['HtmlBody']
    link = list(document_fromstring(message).iterlinks())[0][2]
    token = link.split('token=')[1]

    reset_page = client.get(link)
    assert token in reset_page.text

    reset_page.form['email'] = 'someone_else@example.org'
    reset_page.form['password'] = 'known_very_secure_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Adresse oder abgelaufener Link" in reset_page
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = '1234'
    reset_page = reset_page.form.submit()
    assert "Das Passwort muss mindestens zehn Zeichen lang sein" in reset_page
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'qwertqwert123'
    reset_page = reset_page.form.submit()
    assert ("Das gewünschte Passwort befindet sich auf einer Liste"
    ) in reset_page.text
    assert token in reset_page.text

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'known_very_secure_password'
    assert "Passwort geändert" in reset_page.form.submit()

    reset_page.form['email'] = 'admin@example.org'
    reset_page.form['password'] = 'known_very_secure_password'
    reset_page = reset_page.form.submit()
    assert "Ungültige Adresse oder abgelaufener Link" in reset_page

    login_page = client.get('/auth/login')
    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page = login_page.form.submit()
    assert "Unbekannter Benutzername oder falsches Passwort" in login_page

    login_page.form['username'] = 'admin@example.org'
    login_page.form['password'] = 'known_very_secure_password'
    login_page = login_page.form.submit().follow()
    assert "Sie sind angemeldet" in login_page


def test_view_manage_screens(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage/screens', expect_errors=True).status_code == 403

    login(client)

    manage = client.get('/manage/screens')

    assert 'Noch keine Screens' in manage

    # Add two votes
    new = client.get('/manage/votes').click('Neue Abstimmung')
    new.form['title_de'] = 'Einfache Vorlage'
    new.form['type'] = 'simple'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'federation'
    new.form.submit().follow()

    new = client.get('/manage/votes').click('Neue Abstimmung')
    new.form['title_de'] = 'Vorlage mit Gegenentwurf'
    new.form['type'] = 'complex'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'federation'
    new.form.submit().follow()

    # Add two elections
    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['title_de'] = 'Majorz Wahl'
    new.form['date'] = '2016-01-01'
    new.form['type'] = 'majorz'
    new.form['domain'] = 'municipality'
    new.form['mandates'] = 10
    new.form.submit().follow()

    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['title_de'] = 'Proporz Wahl'
    new.form['date'] = '2016-01-01'
    new.form['type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form['mandates'] = 5
    new.form.submit().follow()

    # Add a compound
    new = client.get('/manage/election-compounds').click('Neue Verbindung')
    new.form['title_de'] = 'Verbund von Wahlen'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'municipality'
    new.form['municipality_elections'] = ['proporz-wahl']
    new.form.submit().follow()

    # Add a screen
    new = client.get('/manage/screens').click('Neuer Screen')
    new.form['number'] = '5'
    new.form['description'] = 'Mein Screen'
    new.form['type'] = 'majorz_election'
    new.form['majorz_election'] = 'majorz-wahl'
    new.form['structure'] = '<model-title />'
    new.form['css'] = '/* Custom CSS */'
    manage = new.form.submit().follow()
    assert 'Mein Screen' in manage
    assert 'Majorz Wahl' in manage

    edit = manage.click('Bearbeiten')
    edit.form['type'] = 'proporz_election'
    edit.form['proporz_election'] = 'proporz-wahl'
    manage = edit.form.submit().follow()
    assert 'Majorz Wahl' not in manage
    assert 'Proporz Wahl' in manage

    edit = manage.click('Bearbeiten')
    edit.form['type'] = 'election_compound'
    edit.form['election_compound'] = 'verbund-von-wahlen'
    manage = edit.form.submit().follow()
    assert 'Majorz Wahl' not in manage
    assert 'Proporz Wahl' not in manage
    assert 'Verbund von Wahlen' in manage

    edit = manage.click('Bearbeiten')
    edit.form['type'] = 'simple_vote'
    edit.form['simple_vote'] = 'einfache-vorlage'
    manage = edit.form.submit().follow()
    assert 'Majorz Wahl' not in manage
    assert 'Proporz Wahl' not in manage
    assert 'Verbund von Wahlen' not in manage
    assert 'Einfache Vorlage' in manage

    edit = manage.click('Bearbeiten')
    edit.form['type'] = 'complex_vote'
    edit.form['complex_vote'] = 'vorlage-mit-gegenentwurf'
    manage = edit.form.submit().follow()
    assert 'Majorz Wahl' not in manage
    assert 'Proporz Wahl' not in manage
    assert 'Verbund von Wahlen' not in manage
    assert 'Einfache Vorlage' not in manage
    assert 'Vorlage mit Gegenentwurf' in manage

    export = manage.click('Export')
    assert export.text == (
        'number,description,type,structure,css,group,duration\r\n'
        '5,Mein Screen,complex_vote,<model-title />,/* Custom CSS */,,\r\n'
    )

    delete = manage.click('Löschen')
    assert 'Screen löschen' in delete
    assert 'Bearbeiten' in delete.click('Abbrechen')

    manage = delete.form.submit().follow()
    assert 'Noch keine Screens' in manage


def test_view_manage_cache(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client, canton='zg')
    logout(client)

    client.get('/vote/vote').follow()
    assert election_day_app_zg.pages_cache.keys()

    login(client)
    client.get('/clear-cache').form.submit().follow()
    assert not election_day_app_zg.pages_cache.keys()
