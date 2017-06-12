from datetime import date
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.tests import login
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
